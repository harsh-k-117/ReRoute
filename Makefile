# Lane: ALL (root). Stack: uv (Python 3.12) + pnpm (Node LTS). Everything runs offline.
.PHONY: install dev check lint test fuzz types build demo bench

install:
	uv sync --extra dev
	cd frontend && pnpm install

dev:           ## API with mock mode + UI dev server
	(REROUTE_MOCK=1 uv run uvicorn api.main:app --reload --port 8000 &) && cd frontend && pnpm dev

lint:
	uv run ruff check .

test:
	uv run pytest

fuzz:          ## 1,000+ Hypothesis cases
	uv run pytest tests/property --hypothesis-seed=0

types:         ## OpenAPI -> TypeScript
	./scripts/gen_types.sh

build:
	cd frontend && pnpm build

check: lint test   ## merge gate: ruff, pytest, tsc, build
	cd frontend && pnpm typecheck && pnpm build

demo:          ## one-command offline demo
	./scripts/demo.sh

bench:         ## optimality gap (brute force) + OR-Tools comparison (star)
	uv run --extra bench python -m engine.benchmarks.bruteforce
