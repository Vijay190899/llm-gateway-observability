.PHONY: install lint format test run up down bench frontend help

help:
	@echo "install  - create venv and install deps with uv"
	@echo "lint     - ruff check + format check"
	@echo "format   - ruff format"
	@echo "test     - run pytest"
	@echo "run      - start the gateway API only"
	@echo "bench    - run the caching benchmark against a running gateway"
	@echo "frontend - run the dashboard dev server (Vite)"
	@echo "up       - start the full local stack (gateway + Redis + dashboard)"
	@echo "down     - stop the local stack"

install:
	uv sync --extra dev

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff format .

test:
	uv run pytest

run:
	uv run uvicorn llmgateway.app:app --reload --port 8000

bench:
	uv run python scripts/benchmark.py

frontend:
	cd frontend && npm install && npm run dev

up:
	docker compose up --build

down:
	docker compose down
