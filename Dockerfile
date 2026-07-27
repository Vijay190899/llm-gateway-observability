FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# README/LICENSE are referenced by pyproject metadata, so the build needs them.
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN uv sync --no-dev

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000
CMD ["uvicorn", "llmgateway.app:app", "--host", "0.0.0.0", "--port", "8000"]
