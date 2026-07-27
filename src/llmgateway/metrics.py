"""Cost / latency / cache metrics, computed over a time window.

Every request appends one event to a rolling buffer. The dashboard asks for a
window (last 30m ... 24h) and `summary()` derives everything from the events
inside it: headline totals, per-model spend, a bucketed time series (requests,
cost, latency), a latency histogram, and a guardrail-findings breakdown.

Reading from the event buffer (one list read + in-process aggregation) keeps
writes cheap and makes every view consistently windowable. A rolling buffer is
the pragmatic store for a demo; a production build would push events to a real
time-series store and query that instead.
"""

from __future__ import annotations

import json
import random
import time
from dataclasses import asdict, dataclass, field

from . import pricing
from .store import Backend

_EVENTS = "metrics:events"
_CAP = 12000  # rolling buffer size

OWASP = {
    "LLM01": "Prompt injection",
    "LLM02": "Insecure output",
    "LLM06": "PII disclosure",
}

# Latency histogram edges in ms (last bin is open-ended).
_LAT_EDGES = [0, 1, 2, 5, 10, 25, 50, 100, 250, 500]


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
    await backend.rpush(_EVENTS, json.dumps(asdict(event)))
    await backend.ltrim(_EVENTS, -_CAP, -1)


def _pct(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    k = min(len(s) - 1, int(round((p / 100.0) * (len(s) - 1))))
    return s[k]


def _avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


async def _load_window(backend: Backend, window_seconds: int) -> tuple[list[dict], float]:
    now = time.time()
    raw = await backend.lrange(_EVENTS, -_CAP, -1)
    start = now - window_seconds
    events = []
    for r in raw:
        e = json.loads(r)
        if e["ts"] >= start:
            events.append(e)
    return events, now


async def summary(backend: Backend, window_seconds: int, buckets: int = 32) -> dict:
    events, now = await _load_window(backend, window_seconds)
    start = now - window_seconds

    requests = len(events)
    hits = sum(1 for e in events if e["cache_hit"])
    blocked = sum(1 for e in events if e["blocked"])
    cost = sum(e["cost_usd"] for e in events)
    saved = sum(e.get("saved_usd", 0.0) for e in events)
    tokens = sum(e["prompt_tokens"] + e["completion_tokens"] for e in events)
    latencies = [e["latency_ms"] for e in events if not e["blocked"]]

    # Per-model spend.
    models: dict[str, dict] = {}
    for e in events:
        m = models.setdefault(e["model"], {"model": e["model"], "requests": 0, "cost_usd": 0.0})
        m["requests"] += 1
        m["cost_usd"] += e["cost_usd"]
    by_model = sorted(
        ({**m, "cost_usd": round(m["cost_usd"], 6)} for m in models.values()),
        key=lambda x: -x["cost_usd"],
    )

    # Per-team spend.
    teams: dict[str, dict] = {}
    for e in events:
        tm = teams.setdefault(e["team"], {"team": e["team"], "requests": 0, "cost_usd": 0.0})
        tm["requests"] += 1
        tm["cost_usd"] += e["cost_usd"]
    by_team = sorted(
        ({**t, "cost_usd": round(t["cost_usd"], 6)} for t in teams.values()),
        key=lambda x: -x["cost_usd"],
    )

    # Bucketed time series.
    size = window_seconds / buckets
    slots = [
        {"lat": [], "requests": 0, "hits": 0, "misses": 0, "cost_usd": 0.0, "tokens": 0}
        for _ in range(buckets)
    ]
    for e in events:
        i = int((e["ts"] - start) / size)
        i = max(0, min(buckets - 1, i))
        s = slots[i]
        s["requests"] += 1
        s["cost_usd"] += e["cost_usd"]
        s["tokens"] += e["prompt_tokens"] + e["completion_tokens"]
        if e["cache_hit"]:
            s["hits"] += 1
        else:
            s["misses"] += 1
        if not e["blocked"]:
            s["lat"].append(e["latency_ms"])
    series = [
        {
            "t": start + (i + 0.5) * size,
            "requests": s["requests"],
            "hits": s["hits"],
            "misses": s["misses"],
            "cost_usd": round(s["cost_usd"], 6),
            "tokens": s["tokens"],
            "avg_latency_ms": round(_avg(s["lat"]), 2),
            "p95_latency_ms": round(_pct(s["lat"], 95), 2),
        }
        for i, s in enumerate(slots)
    ]

    # Latency histogram.
    histogram = []
    for lo, hi in zip(_LAT_EDGES, _LAT_EDGES[1:] + [float("inf")], strict=True):
        count = sum(1 for v in latencies if lo <= v < hi)
        label = f"{lo}+" if hi == float("inf") else f"{lo}-{hi}"
        histogram.append({"lo": lo, "label": label, "count": count})

    # Guardrail findings breakdown by OWASP category.
    findings = {code: 0 for code in OWASP}
    for e in events:
        codes = {f.split(":")[0] for f in e.get("findings", [])}
        for code in codes & findings.keys():
            findings[code] += 1
    findings_out = [{"code": code, "label": OWASP[code], "count": findings[code]} for code in OWASP]

    return {
        "generated_at": now,
        "window_seconds": window_seconds,
        "totals": {
            "requests": requests,
            "cache_hits": hits,
            "cache_hit_rate": round(hits / requests, 4) if requests else 0.0,
            "blocked": blocked,
            "cost_usd": round(cost, 6),
            "saved_usd": round(saved, 6),
            "tokens": tokens,
            "avg_latency_ms": round(_avg(latencies), 1),
            "p95_latency_ms": round(_pct(latencies, 95), 1),
        },
        "series": series,
        "by_model": by_model,
        "by_team": by_team,
        "latency_histogram": histogram,
        "findings": findings_out,
        "recent": list(reversed(events))[:100],
    }


async def seed_synthetic(backend: Backend, hours: int, count: int) -> int:
    """Backfill synthetic history spread across the last `hours` so the time
    filter and time-series charts are demonstrable. Demo utility only."""
    rng = random.Random()
    now = time.time()
    span = hours * 3600
    hot_models = ["mock-gpt", "mock-claude", "gpt-4o-mini", "claude-haiku-4"]
    teams = ["checkout", "search", "support", "billing"]
    for _ in range(count):
        # Bias toward more recent traffic (quadratic) so charts look alive.
        ts = now - span * (rng.random() ** 1.7)
        model = rng.choices(hot_models, weights=[5, 3, 2, 2])[0]
        team = rng.choice(teams)
        cache_hit = rng.random() < 0.46
        blocked = rng.random() < 0.03
        findings: list[str] = []
        if blocked:
            findings = ["LLM01:override-instructions"]
            pt = ct = 0
            cost = 0.0
            saved = 0.0
            lat = rng.uniform(0.5, 2.0)
        elif cache_hit:
            pt = rng.randint(40, 260)
            ct = rng.randint(80, 420)
            cost = 0.0
            saved = pricing.cost_usd(model, pt, ct)
            lat = rng.uniform(0.4, 3.0)
            if rng.random() < 0.06:
                findings = ["LLM06:email"]
        else:
            pt = rng.randint(40, 260)
            ct = rng.randint(80, 420)
            cost = pricing.cost_usd(model, pt, ct)
            saved = 0.0
            lat = rng.uniform(12, 45)
            if rng.random() < 0.05:
                findings = ["LLM06:email"]
            elif rng.random() < 0.04:
                findings = ["LLM02:script-tag"]
        await record(
            backend,
            RequestEvent(
                ts=ts,
                team=team,
                model=model,
                prompt_tokens=pt,
                completion_tokens=ct,
                cost_usd=cost,
                latency_ms=round(lat, 2),
                cache_hit=cache_hit,
                blocked=blocked,
                saved_usd=saved,
                findings=findings,
            ),
        )
    # Buffer is time-ordered by append; sort by ts so windowing/series are correct.
    raw = await backend.lrange(_EVENTS, -_CAP, -1)
    events = sorted((json.loads(r) for r in raw), key=lambda e: e["ts"])
    await backend.ltrim(_EVENTS, 1, 0)  # clear
    for e in events:
        await backend.rpush(_EVENTS, json.dumps(e))
    return count
