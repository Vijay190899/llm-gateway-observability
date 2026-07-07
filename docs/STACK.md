# Stack

What this uses and why.

## Language & runtime
- **Python 3.12**
- **uv** for packaging.

## Gateway
- **FastAPI** — async proxy in front of the LLM providers.
- **Uvicorn** — ASGI server.
- **httpx** — async upstream calls to providers.
- **Pydantic / pydantic-settings** — request models and config.

## Caching & state
- **Redis** — semantic cache store (embedding cosine similarity), plus rate-limiter counters.

## Guardrails
- Prompt-injection detection, PII/output filtering, OWASP-LLM-Top-10 checks enforced inline on request and response.

## Observability
- **Langfuse** — traces every call; dashboards for cost and latency per team/model.
- LLM-as-a-judge scoring on a sample of traffic to catch quality drift.

## Protocols
- **MCP** — the gateway can proxy and route MCP tool calls, so it can front an agent fleet, not just completions.

## Ops & deployment
- **Docker Compose** — local stack (gateway + Redis + Langfuse + mock LLM server).
- **AWS EKS** — production, deployed via a **Helm** chart with **Terraform** for the infra. Compose is dev; Kubernetes is prod.
- **GitHub Actions** — build image, lint, test, deploy.

## Deliverables that prove it works
- Benchmark script showing latency reduction and cost reduction from caching.
- Docs: setup, alert thresholds, dashboards.
