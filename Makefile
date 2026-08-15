.PHONY: api app

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

test:
	uv run pytest
