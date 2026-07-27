# LLM gateway and observability platform

Once more than one team at a company starts shipping LLM features, the same problems show up every time. Nobody knows the monthly spend until the invoice lands. Latency is a guess. The same prompt gets paid for a hundred times a day. When something hallucinates, there's no trail to follow. The model calls are scattered across services with no single place that sees them.

The fix is a gateway: one proxy that every LLM call goes through, so caching, cost tracking, rate limiting, guardrails, and tracing live in one place instead of being rebuilt by every team. That's what this project is, and it's the one where I treat the infrastructure as the product.

## What it does

- Sits in front of the LLM providers as a single FastAPI proxy that teams call instead of the provider directly.
- Semantic cache: if a new request is close enough to one it already answered (embedding cosine similarity, keyed in Redis), it serves the cached response instead of paying for the call again.
- Cost and latency tracking per request, per team, per model.
- Rate limiting, so one runaway job can't drain the budget.
- Guardrails in the request path: prompt-injection detection, PII and output filtering, and an OWASP LLM Top 10 checklist enforced on the way in and out.
- Tracing: every call streamed to Langfuse, with an LLM judge scoring a sample for quality drift.
- MCP-aware: it can route MCP tool calls, not just raw completions, so it can sit in front of a whole agent fleet.

## Why I'm building it this way

- A gateway, not a library. A library each team imports drifts out of sync. A proxy is the one place you can actually enforce policy.
- Semantic caching, not just exact match. Exact-match caching barely helps with natural-language prompts. Similarity-based caching is where the real savings are, and measuring that saving is one of the deliverables.
- Guardrails belong at the boundary. Runtime is the layer where you catch what evals missed. Putting it in the gateway means every team gets it for free.
- Real orchestration. This one goes past Docker Compose into Kubernetes (EKS) with Helm and Terraform, because "I can deploy and operate this" is half the point.

## Stack

Detail in [docs/STACK.md](docs/STACK.md); architecture and design in [docs/TECHNICAL_DOCUMENTATION.md](docs/TECHNICAL_DOCUMENTATION.md). Short version: Python, FastAPI, Redis, Langfuse, Docker Compose for local, then AWS EKS with Helm and Terraform, GitHub Actions CI.

## Status

Work in progress, in the open. Core platform is built and runs end to end.

- [x] FastAPI proxy and provider routing (mock provider by default, real OpenAI/Anthropic when a key is set)
- [x] Redis semantic cache — LSH-indexed for sub-linear lookup, TTL eviction
- [x] Rate limiter and cost/latency metrics
- [x] Guardrails layer (prompt-injection, PII, OWASP LLM Top 10)
- [x] MCP tool-call routing
- [x] Observability dashboard (React) with a live Playground
- [x] Docker Compose stack (gateway + Redis + dashboard)
- [x] Benchmark: latency and cost with and without caching
- [~] Langfuse tracing and LLM-judge sampling (optional, behind a Compose profile)
- [ ] EKS, Helm, Terraform, CI/CD

The gateway is stateless (all state in Redis) and was load-tested at 5,000 concurrent requests with zero errors; cache hits returned in ~2 ms with thousands of entries live. Design decisions are logged in [DECISIONS.md](DECISIONS.md) and [docs/adr/](docs/adr/).

## Running it locally

The whole stack runs with **no API keys and no spend** — the gateway ships with an in-process mock provider and a local embedding, so caching, guardrails, cost tracking and the dashboard all work offline. Add real provider keys to `.env` to route real traffic through the same path.

```bash
docker compose up --build
# Dashboard:  http://localhost:8080
# Gateway API: http://localhost:8000  (POST /v1/chat/completions, GET /metrics, GET /health)
```

Optional tracing (Langfuse): `docker compose --profile tracing up --build`.

### Backend without Docker

```bash
make install          # uv sync (Python 3.12)
make test             # pytest
make run              # gateway on :8000 (uses in-memory backend if Redis is absent)
make bench            # fire a concurrent request mix and report cache savings
```

### Frontend dev

```bash
cd frontend && npm install && npm run dev   # Vite dev server on :5173, proxies to the gateway
```

## Licence

MIT. See [LICENSE](LICENSE).
