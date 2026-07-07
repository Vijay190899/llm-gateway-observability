.PHONY: install lint format test run up down docker help

help:
	@echo "install  - create venv and install deps with uv"
	@echo "lint     - ruff check + format check"
	@echo "format   - ruff format"
	@echo "test     - run pytest"
	@echo "run      - start the gateway API only"
	@echo "up       - start the full local stack (compose)"
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

up:
	docker compose up --build

down:
	docker compose down
