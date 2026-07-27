"""Fixed-window rate limiter."""

from llmgateway import ratelimit as rl
from llmgateway.store import MemoryBackend


async def test_allows_up_to_limit_then_blocks():
    backend = MemoryBackend()
    for _ in range(3):
        decision = await rl.check(backend, "team-a", limit_per_minute=3)
        assert decision.allowed
    blocked = await rl.check(backend, "team-a", limit_per_minute=3)
    assert not blocked.allowed
    assert blocked.remaining == 0


async def test_teams_have_independent_budgets():
    backend = MemoryBackend()
    await rl.check(backend, "team-a", limit_per_minute=1)
    over = await rl.check(backend, "team-a", limit_per_minute=1)
    assert not over.allowed
    other = await rl.check(backend, "team-b", limit_per_minute=1)
    assert other.allowed
