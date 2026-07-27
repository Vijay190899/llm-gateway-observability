"""Fixed-window per-key rate limiting, counters in the storage backend.

One runaway job shouldn't drain a team's budget. Keyed per team per calendar
minute; the counter self-expires so no cleanup is needed.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from .store import Backend


@dataclass
class RateDecision:
    allowed: bool
    remaining: int
    limit: int


async def check(backend: Backend, team: str, limit_per_minute: int) -> RateDecision:
    window = int(time.time() // 60)
    key = f"rl:{team}:{window}"
    count = await backend.incr(key)
    if count == 1:
        await backend.expire(key, 60)
    remaining = max(0, limit_per_minute - count)
    return RateDecision(
        allowed=count <= limit_per_minute, remaining=remaining, limit=limit_per_minute
    )
