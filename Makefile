.PHONY: install run test lint format typecheck check clean

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

typecheck:
	uv run ty check src/

check: lint format typecheck test

clean:
	rm -rf .venv
