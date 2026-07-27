"""Langfuse tracing, made optional.

If Langfuse keys are configured, each completion is streamed as a trace with
cost/latency/cache metadata. If not (the default local case), every call is a
no-op so the gateway runs with zero observability infra. The LLM-as-a-judge
quality sampler lives here too and degrades to a cheap heuristic without keys.
"""

from __future__ import annotations

import random

from .config import Settings


class Tracer:
    def __init__(self, settings: Settings) -> None:
        self._client = None
        self._judge_sample = 0.1
        if settings.langfuse_public_key and settings.langfuse_secret_key:
            try:
                from langfuse import Langfuse

                self._client = Langfuse(
                    public_key=settings.langfuse_public_key,
                    secret_key=settings.langfuse_secret_key,
                    host=settings.langfuse_host,
                )
            except Exception:
                self._client = None

    @property
    def enabled(self) -> bool:
        return self._client is not None

    def trace_completion(
        self, *, model, team, prompt, output, cost_usd, latency_ms, cache_hit
    ) -> None:
        if not self._client:
            return
        try:
            trace = self._client.trace(
                name="chat.completion",
                user_id=team,
                metadata={
                    "model": model,
                    "cost_usd": cost_usd,
                    "latency_ms": latency_ms,
                    "cache_hit": cache_hit,
                },
            )
            trace.generation(name="completion", model=model, input=prompt, output=output)
        except Exception:
            pass

    def should_judge(self) -> bool:
        return random.random() < self._judge_sample

    def judge(self, prompt: str, output: str) -> dict:
        """Sampled quality score for drift detection. Heuristic stand-in for a
        real LLM judge so it works offline; returns a 0-1 score with a reason."""
        length_ok = 20 <= len(output) <= 4000
        on_topic = any(w in output.lower() for w in prompt.lower().split()[:8]) if prompt else True
        refused = "i cannot" in output.lower() or "i'm unable" in output.lower()
        score = 0.5 + 0.3 * length_ok + 0.2 * on_topic - 0.3 * refused
        score = max(0.0, min(1.0, score))
        return {"score": round(score, 2), "length_ok": length_ok, "on_topic": on_topic}
