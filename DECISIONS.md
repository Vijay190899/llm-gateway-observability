# Decisions

Running log, newest first. Non-obvious trade-offs get a full record under [docs/adr/](docs/adr/).

| Date | Decision | Notes |
|---|---|---|
| 2026-07-27 | LSH-indexed cache + stateless gateway for scale | Sub-linear cache lookup, TTL eviction, shared Redis state so the gateway scales horizontally. Verified at 5k concurrent. See [ADR-0004](docs/adr/0004-scaling-the-semantic-cache-and-gateway.md). |
| 2026-07-27 | Single request pipeline in the gateway | Guardrails-in → cache → rate limit → upstream → guardrails-out → metrics → trace, all in one place ([app.py](src/llmgateway/app.py)). Boundary enforcement is the whole point of a proxy. |
| 2026-07-27 | Local embedding + mock provider as offline defaults | Stack runs end-to-end with no API keys or spend; both boundaries stay pluggable. See [ADR-0003](docs/adr/0003-pluggable-local-embedding-and-mock-provider.md). |
| 2026-07-27 | One storage abstraction, Redis with in-memory fallback | Runs and tests with zero infra; nothing outside `store.py` touches redis. See [ADR-0002](docs/adr/0002-storage-backend-with-in-memory-fallback.md). |
| 2026-07-27 | Guardrail findings tagged with OWASP LLM Top 10 ids | Injection=LLM01, insecure output=LLM02, PII disclosure=LLM06; makes the checklist auditable in traces and the dashboard. |
| 2026-07-07 | Adopt lightweight ADRs | See [ADR-0001](docs/adr/0001-record-architecture-decisions.md). |
| 2026-07-07 | Gateway (proxy) over a shared client library | A proxy is the one place policy can actually be enforced; a library drifts per team. |
| 2026-07-07 | Semantic cache, not exact-match | Exact-match rarely hits on NL prompts; similarity-based caching is where the savings are. |
| 2026-07-07 | Kubernetes (EKS) as the prod target | Compose stays for dev; the project's point is showing I can deploy and operate this. |

_Add a row when you make a call worth remembering._
