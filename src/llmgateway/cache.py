"""Semantic cache, scalable by design.

Exact-match caching barely hits on natural-language prompts, so we key on
embedding cosine similarity. To stay fast as the cache grows, lookup does not
scan every entry: an LSH index (`lsh.py`) narrows the search to the small set of
candidates that share a bucket with the query, so lookup cost tracks the number
of *near-duplicates*, not the total cache size.

Entries expire by TTL rather than a manual global trim, so eviction needs no
sweep and memory stays bounded under sustained load. Bucket membership that
outlives its entry is cleaned up lazily on the next probe. All state lives in
the backend (Redis in production), so any number of gateway replicas share one
cache and the gateway stays stateless and horizontally scalable.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass

from . import embeddings, lsh
from .store import Backend

# Cap candidates compared per lookup so a hot bucket can never make a single
# request unbounded. Recall is preserved by the L independent LSH tables.
_MAX_CANDIDATES = 200


@dataclass
class CacheHit:
    response: dict
    similarity: float
    original_cost_usd: float


async def lookup(backend: Backend, prompt: str, threshold: float) -> CacheHit | None:
    query = embeddings.embed(prompt)
    bucket_keys = lsh.bucket_keys(query)

    # Gather candidate entry keys from the query's buckets (union across tables).
    candidates: list[tuple[str, str]] = []
    seen: set[str] = set()
    for bkey in bucket_keys:
        for entry_key in await backend.smembers(bkey):
            if entry_key not in seen:
                seen.add(entry_key)
                candidates.append((entry_key, bkey))
            if len(candidates) >= _MAX_CANDIDATES:
                break
        if len(candidates) >= _MAX_CANDIDATES:
            break

    best: CacheHit | None = None
    best_sim = threshold
    for entry_key, bkey in candidates:
        raw = await backend.get(entry_key)
        if not raw:
            # Entry expired but its bucket membership lingers; clean it up.
            await backend.srem(bkey, entry_key)
            continue
        entry = json.loads(raw)
        sim = embeddings.cosine(query, entry["embedding"])
        if sim >= best_sim:
            best_sim = sim
            best = CacheHit(
                response=entry["response"],
                similarity=round(sim, 4),
                original_cost_usd=entry.get("cost_usd", 0.0),
            )
    return best


async def store(
    backend: Backend,
    prompt: str,
    response: dict,
    model: str,
    cost_usd: float,
    ttl_seconds: int = 3600,
) -> None:
    vec = embeddings.embed(prompt)
    entry_id = uuid.uuid4().hex
    entry_key = f"cache:e:{entry_id}"
    entry = {
        "embedding": vec,
        "response": response,
        "model": model,
        "cost_usd": cost_usd,
        "ts": time.time(),
    }
    await backend.set(entry_key, json.dumps(entry), ex=ttl_seconds)
    for bkey in lsh.bucket_keys(vec):
        # Buckets outlive entries slightly, then expire; stale members are also
        # pruned lazily on lookup.
        await backend.sadd(bkey, entry_key, ex=ttl_seconds * 2)
