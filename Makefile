.PHONY: install run test lint format format-check typecheck audit docs docs-build docker check clean

install:
	uv sync

run:
	WOODPECKER_SERVER=$(WOODPECKER_SERVER) uv run woodpecker-mcp

test:
	uv run pytest -v

lint:
	uv run ruff check src/ tests/

format:
	uv run ruff format src/ tests/

format-check:
	uv run ruff format --check src/ tests/

typecheck:
	uv run ty check src/ tests/

audit:
	uv audit

docs:
	uv sync --group docs
	uv run mkdocs serve

docs-build:
	uv sync --group docs
	uv run mkdocs build --strict

docker:
	docker build -t woodpecker-mcp .

check: lint format-check typecheck test

clean:
	rm -rf .venv
