# Decisions

Running log, newest first. Non-obvious trade-offs get a full record under [docs/adr/](docs/adr/).

| Date | Decision | Notes |
|---|---|---|
| 2026-07-07 | Adopt lightweight ADRs | See [ADR-0001](docs/adr/0001-record-architecture-decisions.md). |
| 2026-07-07 | Gateway (proxy) over a shared client library | A proxy is the one place policy can actually be enforced; a library drifts per team. |
| 2026-07-07 | Semantic cache, not exact-match | Exact-match rarely hits on NL prompts; similarity-based caching is where the savings are. |
| 2026-07-07 | Kubernetes (EKS) as the prod target | Compose stays for dev; the project's point is showing I can deploy and operate this. |

_Add a row when you make a call worth remembering._
