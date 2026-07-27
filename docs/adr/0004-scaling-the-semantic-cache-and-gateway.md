# ADR-0004: Scaling the semantic cache and the gateway

- **Status:** Accepted
- **Date:** 2026-07-27

## Context

A semantic cache is only useful if looking something up is cheaper than the call
it avoids. The obvious implementation — embed the prompt, then compare against
every stored entry — is O(n) per request. As the cache fills, every request gets
slower, so the feature degrades exactly when traffic (and the payoff) is highest.
That is a toy, not a system.

Separately, the gateway itself has to handle real concurrent load and scale out,
not just serve a demo.

## Decision

**Sub-linear cache lookup via LSH.** Each embedding is indexed with
locality-sensitive hashing (`lsh.py`): random-hyperplane signatures across L
independent hash tables. Near-duplicate prompts share a bucket with high
probability, so a lookup only pulls the candidates in the query's buckets (a
Redis `SMEMBERS` per table) and compares against those — not the whole cache.
Candidates per lookup are capped, and L tables keep recall high. Lookup cost now
tracks the number of near-duplicates, independent of total cache size.

**TTL eviction, not a global trim.** Entries and their bucket membership carry a
TTL and expire on their own; stale bucket members are pruned lazily on the next
probe. No background sweep, and memory stays bounded under sustained load.

**Stateless gateway + shared state in Redis.** Cache, rate-limit counters, and
metrics all live in the backend, never in process memory (the in-memory backend
is a dev-only fallback). So the gateway process holds no request state and scales
horizontally: run N uvicorn workers / N replicas behind a load balancer and they
share one consistent cache and one rate-limit view.

**Pooled upstream connections.** One shared `httpx.AsyncClient` with a keep-alive
pool is reused across all upstream calls, so load doesn't pay a TCP+TLS handshake
per request.

## Consequences

- Verified: 5,000 concurrent requests, 0 errors; cache hits returned in ~2 ms
  while thousands of entries were live — flat lookup latency as the cache grew.
- Rate limiting uses atomic Redis `INCR`, correct across replicas; the in-memory
  fallback is single-process and is reported at `/health` so the limitation is
  never silent.
- Per-core throughput is bounded by the CPU-bound embedding/LSH work on the async
  loop; the answer is more workers/replicas (the design allows it), and a real
  embedding call would be async I/O rather than CPU anyway.
- Known next step: pipeline the per-request metric writes to cut Redis round
  trips; acceptable as-is, called out so it isn't mistaken for finished.
