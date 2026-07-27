"""FastAPI gateway: the single proxy every LLM call goes through.

Request path: guardrails (in) -> semantic cache -> rate limit -> upstream ->
guardrails (out) -> cost/latency metrics -> trace. Everything a team would
otherwise rebuild lives here once.
"""

from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from . import cache, guardrails, mcp, metrics, pricing
from . import ratelimit as rl
from .config import get_settings
from .models import (
    ChatRequest,
    ChatResponse,
    Choice,
    GatewayMeta,
    GuardrailReport,
    MCPToolCall,
    MCPToolResult,
    Message,
    Usage,
)
from .providers import Router
from .store import make_backend
from .tracing import Tracer


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.settings = settings
    app.state.backend = await make_backend(settings.redis_url)
    app.state.router = Router(settings)
    app.state.tracer = Tracer(settings)
    try:
        yield
    finally:
        await app.state.router.aclose()


app = FastAPI(title="LLM Gateway", version="0.1.0", lifespan=lifespan)

_origins = get_settings().cors_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if _origins.strip() == "*" else [o.strip() for o in _origins.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health(request: Request):
    backend = request.app.state.backend
    try:
        ok = await backend.ping()
    except Exception:
        ok = False
    return {
        "status": "ok",
        "backend": type(backend).__name__,
        "redis": type(backend).__name__ == "RedisBackend" and ok,
        "tracing": request.app.state.tracer.enabled,
    }


@app.post("/v1/chat/completions", response_model=ChatResponse)
async def chat_completions(
    body: ChatRequest,
    request: Request,
    x_team: str = Header(default="default"),
):
    started = time.perf_counter()
    settings = request.app.state.settings
    backend = request.app.state.backend
    tracer = request.app.state.tracer

    prompt = "\n".join(m.content for m in body.messages)

    # 1. Guardrails on the way in.
    allowed, in_findings, safe_prompt = guardrails.scan_input(prompt, settings.block_on_injection)
    if not allowed:
        latency_ms = (time.perf_counter() - started) * 1000
        await metrics.record(
            backend,
            metrics.RequestEvent(
                ts=time.time(),
                team=x_team,
                model=body.model,
                prompt_tokens=0,
                completion_tokens=0,
                cost_usd=0.0,
                latency_ms=latency_ms,
                cache_hit=False,
                blocked=True,
                findings=in_findings,
            ),
        )
        raise HTTPException(
            status_code=400, detail={"error": "blocked_by_guardrails", "findings": in_findings}
        )

    # 2. Rate limit (per team).
    decision = await rl.check(backend, x_team, settings.rate_limit_per_minute)
    if not decision.allowed:
        raise HTTPException(
            status_code=429,
            detail={"error": "rate_limit_exceeded", "limit": decision.limit},
            headers={"Retry-After": "60"},
        )

    # 3. Semantic cache lookup.
    hit = await cache.lookup(backend, prompt, settings.cache_similarity_threshold)
    if hit is not None:
        latency_ms = (time.perf_counter() - started) * 1000
        response = ChatResponse(**hit.response)
        response.gateway = GatewayMeta(
            cache_hit=True,
            latency_ms=round(latency_ms, 2),
            cost_usd=0.0,
            team=x_team,
            guardrails=GuardrailReport(allowed=True, input_findings=in_findings),
        )
        await metrics.record(
            backend,
            metrics.RequestEvent(
                ts=time.time(),
                team=x_team,
                model=body.model,
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                cost_usd=0.0,
                latency_ms=latency_ms,
                cache_hit=True,
                blocked=False,
                saved_usd=hit.original_cost_usd,
                findings=in_findings,
            ),
        )
        return response

    # 4. Upstream call.
    completion = await request.app.state.router.complete(body)

    # 5. Guardrails on the way out.
    out_findings, safe_output = guardrails.scan_output(completion.text)

    cost = pricing.cost_usd(body.model, completion.prompt_tokens, completion.completion_tokens)
    latency_ms = (time.perf_counter() - started) * 1000
    redacted = any(f.startswith("LLM06") for f in in_findings + out_findings)

    response = ChatResponse(
        id="chatcmpl-" + uuid.uuid4().hex[:24],
        model=body.model,
        choices=[Choice(message=Message(role="assistant", content=safe_output))],
        usage=Usage(
            prompt_tokens=completion.prompt_tokens,
            completion_tokens=completion.completion_tokens,
            total_tokens=completion.prompt_tokens + completion.completion_tokens,
        ),
        gateway=GatewayMeta(
            cache_hit=False,
            latency_ms=round(latency_ms, 2),
            cost_usd=cost,
            team=x_team,
            guardrails=GuardrailReport(
                allowed=True,
                input_findings=in_findings,
                output_findings=out_findings,
                redacted=redacted,
            ),
        ),
    )

    # 6. Store in cache for next time (keyed on the original prompt).
    await cache.store(
        backend, prompt, response.model_dump(), body.model, cost, settings.cache_ttl_seconds
    )

    # 7. Metrics + trace.
    await metrics.record(
        backend,
        metrics.RequestEvent(
            ts=time.time(),
            team=x_team,
            model=body.model,
            prompt_tokens=completion.prompt_tokens,
            completion_tokens=completion.completion_tokens,
            cost_usd=cost,
            latency_ms=latency_ms,
            cache_hit=False,
            blocked=False,
            findings=in_findings + out_findings,
        ),
    )
    tracer.trace_completion(
        model=body.model,
        team=x_team,
        prompt=safe_prompt,
        output=safe_output,
        cost_usd=cost,
        latency_ms=latency_ms,
        cache_hit=False,
    )
    if tracer.should_judge():
        response.gateway.guardrails.output_findings.append(
            "judge:score=" + str(tracer.judge(prompt, safe_output)["score"])
        )
    return response


@app.post("/v1/mcp/call", response_model=MCPToolResult)
async def mcp_call(body: MCPToolCall, request: Request, x_team: str = Header(default="default")):
    backend = request.app.state.backend
    settings = request.app.state.settings
    decision = await rl.check(backend, x_team, settings.rate_limit_per_minute)
    if not decision.allowed:
        raise HTTPException(status_code=429, detail={"error": "rate_limit_exceeded"})

    started = time.perf_counter()
    try:
        result = mcp.call_tool(body.tool, body.arguments)
        error = None
    except KeyError:
        raise HTTPException(
            status_code=404, detail={"error": "unknown_tool", "tools": mcp.available_tools()}
        ) from None
    except Exception as exc:  # noqa: BLE001 - surface tool errors to caller
        result, error = None, str(exc)
    latency_ms = (time.perf_counter() - started) * 1000
    return MCPToolResult(
        tool=body.tool, result=result, latency_ms=round(latency_ms, 2), error=error
    )


@app.get("/v1/mcp/tools")
async def mcp_tools():
    return {"tools": mcp.available_tools()}


@app.get("/metrics")
async def get_metrics(request: Request, window: int = 3600):
    # window is a look-back in seconds (30m .. 24h from the dashboard).
    window = max(60, min(window, 86400))
    return await metrics.summary(request.app.state.backend, window)


@app.post("/internal/seed")
async def seed(request: Request, hours: int = 24, count: int = 1500):
    """Demo utility: backfill synthetic history so the time filters and
    time-series charts have something to show. Disabled in production."""
    settings = request.app.state.settings
    if settings.environment == "production":
        raise HTTPException(status_code=403, detail={"error": "seeding disabled in production"})
    hours = max(1, min(hours, 24))
    count = max(1, min(count, 8000))
    n = await metrics.seed_synthetic(request.app.state.backend, hours, count)
    return {"seeded": n, "hours": hours}
