.PHONY: api app content

format:
	uv run ruff format .

lint:
	uv run ruff check .

typecheck:
	uv run ty check

check: format lint typecheck

api:
	uvicorn api.app.main:app --reload

app:
	uv run -m app.main

content:
	uv run -m infra.content.cli

test:
	uv run pytest
