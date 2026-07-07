# LLM gateway & observability platform

Once more than one team at a company starts shipping LLM features, the same mess shows up every time: nobody knows what the monthly spend is until the invoice lands, latency is a mystery, the same prompt gets paid for a hundred times a day, and when something hallucinates there's no trail to follow. The model calls are scattered across services with no single place that sees them.

The fix isn't glamorous — it's a gateway. One proxy that every LLM call goes through, so you get caching, cost tracking, rate limiting, guardrails, and tracing in one place instead of reinventing them per team. That's what I'm building here, and it's the project where I get to treat the *infrastructure* as the product.

## What it does

- Sits in front of the LLM providers as a single **FastAPI proxy** every team calls instead of the provider directly.
- **Semantic cache** — if a new request is close enough to one it's already answered (embedding cosine similarity, keyed in Redis), it serves the cached response instead of paying for the call again.
- **Cost + latency tracking** per request, per team, per model.
- **Rate limiting** so one runaway job can't blow the budget.
- **Guardrails in the request path** — prompt-injection detection, PII/output filtering, and an OWASP-LLM-Top-10 checklist enforced on the way in and out.
- **Tracing** — every call streamed to Langfuse, with LLM-as-a-judge scoring on a sample for quality drift.
- **MCP-aware** — it can route MCP tool calls, not just raw completions, so it can sit in front of a whole agent fleet.

## Why I'm building it this way

- **A gateway, not a library.** A library each team imports drifts out of sync. A proxy is the one place you can actually enforce policy.
- **Semantic caching, not just exact-match.** Exact-match caching barely helps with natural-language prompts. Similarity-based caching is where the real cost savings are — and quantifying that saving is one of the deliverables.
- **Guardrails belong at the boundary.** Runtime is the layer where you catch what evals missed. Putting it in the gateway means every team gets it for free.
- **Real orchestration.** This one goes past Docker Compose into Kubernetes (EKS) with Helm and Terraform, because "I can deploy and operate this" is half the point of the project.

## Stack

Detail in [docs/STACK.md](docs/STACK.md); architecture and design in [docs/TECHNICAL_DOCUMENTATION.md](docs/TECHNICAL_DOCUMENTATION.md). Short version: Python, FastAPI, Redis, Langfuse, Docker Compose for local, then AWS EKS + Helm + Terraform, GitHub Actions CI.

## Status

Work in progress, in the open.

- [ ] FastAPI proxy + provider routing
- [ ] Redis semantic cache
- [ ] Rate limiter + cost/latency metrics
- [ ] Guardrails layer (prompt-injection, PII, OWASP LLM Top-10)
- [ ] Langfuse tracing + LLM-judge sampling
- [ ] MCP tool-call routing
- [ ] Docker Compose stack
- [ ] EKS + Helm + Terraform + CI/CD
- [ ] Benchmark: latency + cost with/without caching

Decisions logged in [DECISIONS.md](DECISIONS.md).

## Running it locally

```bash
make install
cp .env.example .env
make up          # brings up the Compose stack (gateway + Redis + Langfuse + mock LLM)
make test
```

## Licence

MIT — see [LICENSE](LICENSE).
