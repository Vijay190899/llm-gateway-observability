# Stack

What this uses and why.

## Language and runtime
- **Python 3.12**.
- **uv** for packaging.

## Gateway
- **FastAPI** for the async proxy in front of the LLM providers.
- **Uvicorn** as the ASGI server.
- **httpx** for async upstream calls to providers.
- **Pydantic / pydantic-settings** for request models and config.

## Caching and state
- **Redis** for the semantic cache store (embedding cosine similarity), plus rate-limiter counters.

## Guardrails
- Prompt-injection detection, PII and output filtering, and OWASP LLM Top 10 checks enforced inline on request and response.

## Observability
- **Langfuse** traces every call, with dashboards for cost and latency per team and model.
- LLM-as-a-judge scoring on a sample of traffic to catch quality drift.

## Protocols
- **MCP**: the gateway can proxy and route MCP tool calls, so it can front an agent fleet, not just completions.

## Ops and deployment
- **Docker Compose** for the local stack (gateway, Redis, Langfuse, mock LLM server).
- **AWS EKS** for production, deployed via a **Helm** chart with **Terraform** for the infra. Compose is dev, Kubernetes is prod.
- **GitHub Actions**: build image, lint, test, deploy.

## What proves it works
- Benchmark script showing latency reduction and cost reduction from caching.
- Docs for setup, alert thresholds, and dashboards.
