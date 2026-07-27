"""Upstream provider routing.

The gateway normalizes every provider behind one call: `complete(request) ->
(text, usage)`. A built-in mock provider lets the whole stack run end-to-end
with no API keys or spend; real OpenAI-compatible and Anthropic providers are
used automatically when a matching key is configured.
"""

from __future__ import annotations

import asyncio
import hashlib
from dataclasses import dataclass

import httpx

from .config import Settings
from .models import ChatRequest


@dataclass
class Completion:
    text: str
    prompt_tokens: int
    completion_tokens: int


def _estimate_tokens(text: str) -> int:
    # ~4 chars per token is close enough for cost/latency estimation.
    return max(1, len(text) // 4)


class MockProvider:
    """Deterministic, offline stand-in for a real LLM. No network, no cost."""

    async def complete(self, request: ChatRequest) -> Completion:
        prompt = "\n".join(m.content for m in request.messages)
        last_user = next(
            (m.content for m in reversed(request.messages) if m.role == "user"),
            prompt,
        )
        seed = hashlib.md5(last_user.encode()).hexdigest()[:6]
        text = (
            f"[mock:{request.model}] Here is a synthesized answer to: "
            f'"{last_user.strip()[:180]}". '
            f"This response is generated locally for demonstration (ref {seed})."
        )
        # Simulate a small, size-dependent upstream latency.
        await asyncio.sleep(min(0.25, 0.02 + len(prompt) / 20000))
        return Completion(
            text=text,
            prompt_tokens=_estimate_tokens(prompt),
            completion_tokens=_estimate_tokens(text),
        )


class OpenAIProvider:
    def __init__(self, api_key: str, client: httpx.AsyncClient) -> None:
        self._key = api_key
        self._client = client

    async def complete(self, request: ChatRequest) -> Completion:
        resp = await self._client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {self._key}"},
            json={
                "model": request.model,
                "messages": [m.model_dump() for m in request.messages],
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        usage = data.get("usage", {})
        return Completion(
            text=data["choices"][0]["message"]["content"],
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
        )


class AnthropicProvider:
    def __init__(self, api_key: str, client: httpx.AsyncClient) -> None:
        self._key = api_key
        self._client = client

    async def complete(self, request: ChatRequest) -> Completion:
        system = "\n".join(m.content for m in request.messages if m.role == "system")
        turns = [m.model_dump() for m in request.messages if m.role in ("user", "assistant")]
        resp = await self._client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self._key,
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": request.model,
                "system": system,
                "messages": turns,
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        usage = data.get("usage", {})
        return Completion(
            text="".join(block.get("text", "") for block in data.get("content", [])),
            prompt_tokens=usage.get("input_tokens", 0),
            completion_tokens=usage.get("output_tokens", 0),
        )


class Router:
    """Picks a provider by model name, falling back to the mock provider so the
    gateway always answers even without upstream credentials.

    Holds one pooled httpx client shared across all upstream calls: under load,
    connection reuse (keep-alive) avoids a TCP+TLS handshake per request, which
    is where a per-request client would fall over."""

    def __init__(self, settings: Settings) -> None:
        self._client = httpx.AsyncClient(
            timeout=60,
            limits=httpx.Limits(max_connections=200, max_keepalive_connections=50),
        )
        self._mock = MockProvider()
        self._openai = (
            OpenAIProvider(settings.openai_api_key, self._client)
            if settings.openai_api_key
            else None
        )
        self._anthropic = (
            AnthropicProvider(settings.anthropic_api_key, self._client)
            if settings.anthropic_api_key
            else None
        )

    def provider_for(self, model: str):
        if model.startswith("mock"):
            return self._mock
        if model.startswith("claude") and self._anthropic:
            return self._anthropic
        if model.startswith("gpt") and self._openai:
            return self._openai
        return self._mock

    async def complete(self, request: ChatRequest) -> Completion:
        return await self.provider_for(request.model).complete(request)

    async def aclose(self) -> None:
        await self._client.aclose()
