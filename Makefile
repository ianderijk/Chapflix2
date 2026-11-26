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

content-push:
	uv run -m infra.content.cli push-content

content-load:
	uv run -m infra.content.cli load-content

test:
	uv run pytest -vv
