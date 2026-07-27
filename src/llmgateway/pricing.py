"""Per-model token pricing, USD per 1K tokens (input, output).

Approximate public list prices; the point is relative cost visibility, not
invoice-grade accuracy. Unknown models fall back to a default so cost tracking
never silently reports zero.
"""

from __future__ import annotations

_PRICES: dict[str, tuple[float, float]] = {
    "gpt-4o": (0.0025, 0.010),
    "gpt-4o-mini": (0.00015, 0.0006),
    "gpt-4-turbo": (0.010, 0.030),
    "claude-opus-4": (0.015, 0.075),
    "claude-sonnet-4": (0.003, 0.015),
    "claude-haiku-4": (0.0008, 0.004),
    # Mock models priced like a small hosted model so demo cost numbers look real.
    "mock-gpt": (0.00015, 0.0006),
    "mock-claude": (0.0008, 0.004),
}
_DEFAULT = (0.001, 0.002)


def price_for(model: str) -> tuple[float, float]:
    return _PRICES.get(model, _DEFAULT)


def cost_usd(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    in_rate, out_rate = price_for(model)
    return round(prompt_tokens / 1000 * in_rate + completion_tokens / 1000 * out_rate, 6)
