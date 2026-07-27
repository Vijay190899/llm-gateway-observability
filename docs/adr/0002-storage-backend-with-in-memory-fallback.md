# ADR-0002: One storage abstraction, Redis with an in-memory fallback

- **Status:** Accepted
- **Date:** 2026-07-27

## Context

The cache, rate limiter, and metrics all need shared, fast, keyed state. Redis
is the right production store. But requiring a running Redis just to start the
app, run a test, or click through the dashboard raises the cost of every small
loop and makes the code harder to try.

The gateway also shouldn't have Redis calls sprinkled through it — that couples
business logic to one client and makes the fallback impossible.

## Decision

Define one narrow async `Backend` interface (`store.py`) with only the
operations the app actually uses (get/set, incr/expire, hash increments, list
push/trim/range, prefix scan). Provide two implementations behind it:

- `RedisBackend` — thin adapter over `redis.asyncio`.
- `MemoryBackend` — single-process dict-based shim with the same surface.

`make_backend()` tries Redis and **falls back to memory if it is unreachable**.
Nothing outside `store.py` imports redis.

## Consequences

- The gateway and its tests run with zero infrastructure; `make test` needs no
  services, and the API is usable the moment it boots.
- The fallback is not durable or multi-process — acceptable for local/dev, and
  `/health` reports which backend is live so the degraded mode is never silent.
- New state operations must be added to the interface and both backends. The
  interface stays small on purpose to keep that cost low.
- Swapping in a different store later (e.g. a Redis vector index) is a change in
  one file, not the whole request path.
