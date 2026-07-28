.PHONY: api

format:
	uv run ruff format .

lint:
	uv run ruff check .

typecheck:
	uv run ty check

check: format lint typecheck

api:
	uvicorn api.app.routers.player:app --reload

test:
	uv run pytest
