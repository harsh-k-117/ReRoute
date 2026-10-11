.PHONY: setup dev check test fuzz demo types clean

setup:
	uv sync
	@if [ -f frontend/package.json ] && command -v pnpm >/dev/null 2>&1; then cd frontend && pnpm install --frozen-lockfile; fi

dev:
	uv run uvicorn api.main:app --reload

check:
	uv run ruff check .
	uv run ruff format --check .
	uv run pytest -q -m "not slow"
	@if [ -f frontend/package.json ] && command -v pnpm >/dev/null 2>&1; then cd frontend && pnpm exec tsc --noEmit && pnpm build; fi

test:
	uv run pytest -q

fuzz:
	uv run pytest -q -m slow

demo:
	@echo "not built yet"

types:
	bash scripts/gen_types.sh

clean:
	rm -rf .pytest_cache .ruff_cache .coverage htmlcov frontend/dist