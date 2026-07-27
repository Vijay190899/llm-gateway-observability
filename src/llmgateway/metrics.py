"""Cost / latency / cache metrics.

Every request records one event (recent rolling window) and bumps lifetime
totals, broken down per team and per model. `/metrics` reads these back for the
dashboard: headline numbers, per-model spend, and a recent-request feed the UI
turns into charts.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field

from .store import Backend

_RECENT = "metrics:recent"
_TOTALS = "metrics:totals"
_BY_MODEL = "metrics:by_model:"
_BY_TEAM = "metrics:by_team:"
_RECENT_CAP = 500


@dataclass
class RequestEvent:
    ts: float
    team: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    latency_ms: float
    cache_hit: bool
    blocked: bool
    saved_usd: float = 0.0
    findings: list[str] = field(default_factory=list)


async def record(backend: Backend, event: RequestEvent) -> None:
    await backend.rpush(_RECENT, json.dumps(asdict(event)))
    await backend.ltrim(_RECENT, -_RECENT_CAP, -1)

    await backend.hincrbyfloat(_TOTALS, "requests", 1)
    await backend.hincrbyfloat(_TOTALS, "cost_usd", event.cost_usd)
    await backend.hincrbyfloat(_TOTALS, "saved_usd", event.saved_usd)
    await backend.hincrbyfloat(_TOTALS, "latency_ms_sum", event.latency_ms)
    await backend.hincrbyfloat(_TOTALS, "cache_hits", 1 if event.cache_hit else 0)
    await backend.hincrbyfloat(_TOTALS, "blocked", 1 if event.blocked else 0)
    await backend.hincrbyfloat(_TOTALS, "tokens", event.prompt_tokens + event.completion_tokens)

    await backend.hincrbyfloat(_BY_MODEL + event.model, "requests", 1)
    await backend.hincrbyfloat(_BY_MODEL + event.model, "cost_usd", event.cost_usd)
    await backend.hincrbyfloat(_BY_TEAM + event.team, "requests", 1)
    await backend.hincrbyfloat(_BY_TEAM + event.team, "cost_usd", event.cost_usd)


def _num(d: dict[str, str], key: str) -> float:
    try:
        return float(d.get(key, 0) or 0)
    except (TypeError, ValueError):
        return 0.0


async def summary(backend: Backend) -> dict:
    totals = await backend.hgetall(_TOTALS)
    recent_raw = await backend.lrange(_RECENT, -_RECENT_CAP, -1)
    recent = [json.loads(r) for r in recent_raw]

    requests = _num(totals, "requests")
    hits = _num(totals, "cache_hits")

    # Per-model breakdown, discovered from the recent feed and read from totals.
    models: dict[str, dict] = {}
    teams: dict[str, dict] = {}
    for ev in recent:
        models.setdefault(ev["model"], {})
        teams.setdefault(ev["team"], {})
    by_model = []
    for model in models:
        m = await backend.hgetall(_BY_MODEL + model)
        by_model.append(
            {"model": model, "requests": int(_num(m, "requests")), "cost_usd": round(_num(m, "cost_usd"), 6)}
        )
    by_team = []
    for team in teams:
        t = await backend.hgetall(_BY_TEAM + team)
        by_team.append(
            {"team": team, "requests": int(_num(t, "requests")), "cost_usd": round(_num(t, "cost_usd"), 4)}
        )

    return {
        "generated_at": time.time(),
        "totals": {
            "requests": int(requests),
            "cache_hits": int(hits),
            "cache_hit_rate": round(hits / requests, 4) if requests else 0.0,
            "blocked": int(_num(totals, "blocked")),
            "cost_usd": round(_num(totals, "cost_usd"), 6),
            "saved_usd": round(_num(totals, "saved_usd"), 6),
            "tokens": int(_num(totals, "tokens")),
            "avg_latency_ms": round(_num(totals, "latency_ms_sum") / requests, 1) if requests else 0.0,
        },
        "by_model": sorted(by_model, key=lambda x: -x["cost_usd"]),
        "by_team": sorted(by_team, key=lambda x: -x["cost_usd"]),
        "recent": list(reversed(recent))[:100],
    }
