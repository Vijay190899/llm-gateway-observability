"""Caching benchmark: latency, cost and throughput, with vs without the cache.

Fires a representative, concurrent request mix (common prompts recur, as they do
in real traffic) at a running gateway and reports from the gateway's own
per-request metadata. The "without cache" figure is the counterfactual: what
every request would have cost upstream, which the gateway tracks as the saved
amount on each cache hit.

Concurrency exercises the gateway the way real load does. Raise the gateway's
rate limit for a load test, e.g. RATE_LIMIT_PER_MINUTE=1000000.

Usage:
    python scripts/benchmark.py --n 2000 --concurrency 50
"""

from __future__ import annotations

import argparse
import asyncio
import random
import statistics
import time

import httpx

# "Hot" prompts recur across the workload (common FAQs) so the cache can hit.
HOT = [
    "Summarize the quarterly earnings report in three bullet points.",
    "What is the difference between a gateway and a client library?",
    "Explain semantic caching to a new engineer.",
    "How do I rate limit an API per team?",
    "List the OWASP LLM Top 10 risks.",
    "Draft a friendly out-of-office reply.",
]
MODELS = ["mock-gpt", "mock-claude"]
TEAMS = ["checkout", "search", "support"]


def next_prompt(rng: random.Random, i: int) -> str:
    # Half the traffic is a recurring hot prompt; the other half is unique
    # (a novel user question) which the cache cannot hit, a believable mix.
    if rng.random() < 0.5:
        return rng.choice(HOT)
    return f"Explain concept #{i}-{rng.randint(1000, 9999)} for our internal wiki in detail."


async def worker(client, url, jobs, results, errors):
    for _i, content, model, team in jobs:
        try:
            r = await client.post(
                f"{url}/v1/chat/completions",
                headers={"X-Team": team},
                json={"model": model, "messages": [{"role": "user", "content": content}]},
            )
            if r.status_code != 200:
                errors.append(r.status_code)
                continue
            results.append(r.json()["gateway"])
        except Exception as exc:  # noqa: BLE001
            errors.append(str(exc))


async def run(url: str, n: int, concurrency: int, seed: int) -> None:
    rng = random.Random(seed)
    all_jobs = [(i, next_prompt(rng, i), rng.choice(MODELS), rng.choice(TEAMS)) for i in range(n)]
    # Partition round-robin across workers.
    buckets: list[list] = [[] for _ in range(concurrency)]
    for j, job in enumerate(all_jobs):
        buckets[j % concurrency].append(job)

    results: list[dict] = []
    errors: list = []
    print(f"Sending {n} requests at concurrency {concurrency} to {url} ...")
    t0 = time.perf_counter()
    async with httpx.AsyncClient(
        timeout=60, limits=httpx.Limits(max_connections=concurrency + 10)
    ) as client:
        await asyncio.gather(*(worker(client, url, b, results, errors) for b in buckets))
    wall = time.perf_counter() - t0

    if not results:
        print(f"No successful requests. errors={errors[:5]}")
        print("(raise RATE_LIMIT_PER_MINUTE on the gateway for load tests)")
        return

    lat_hit = [g["latency_ms"] for g in results if g["cache_hit"]]
    lat_miss = [g["latency_ms"] for g in results if not g["cache_hit"]]
    billed = sum(g["cost_usd"] for g in results)
    hits = len(lat_hit)
    saved = httpx.get(f"{url}/metrics").json()["totals"]["saved_usd"]
    would_have = billed + saved

    def avg(xs):
        return statistics.mean(xs) if xs else 0.0

    def p95(xs):
        return statistics.quantiles(xs, n=20)[-1] if len(xs) >= 20 else max(xs, default=0.0)

    ok = len(results)
    print("\n=== Results ===")
    print(f"successful:          {ok} / {n}   (errors: {len(errors)})")
    print(f"wall clock:          {wall:.2f}s   throughput: {ok / wall:.0f} req/s")
    print(f"cache hit rate:      {hits / ok * 100:.1f}%")
    print(f"latency miss  avg/p95: {avg(lat_miss):.1f} / {p95(lat_miss):.1f} ms")
    print(f"latency hit   avg/p95: {avg(lat_hit):.2f} / {p95(lat_hit):.2f} ms")
    if avg(lat_hit) and avg(lat_miss):
        print(f"latency reduction:   {(1 - avg(lat_hit) / avg(lat_miss)) * 100:.1f}% on cache hits")
    print("--- cost ---")
    print(f"billed (with cache): ${billed:.6f}")
    print(f"without cache:       ${would_have:.6f}")
    if would_have:
        print(f"cost reduction:      {saved / would_have * 100:.1f}%  (${saved:.6f} saved)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8000")
    ap.add_argument("--n", type=int, default=2000)
    ap.add_argument("--concurrency", type=int, default=50)
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()
    asyncio.run(run(args.url.rstrip("/"), args.n, args.concurrency, args.seed))
