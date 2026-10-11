#!/usr/bin/env bash
# scripts/demo.sh - one-command OFFLINE demo: build UI, serve it from FastAPI with pre-seeded state
# Lane : P3 Integration & language lead
# Stack: bash + Python 3.12 (stdlib argparse) · uv · openapi-typescript
set -euo pipefail
cd "$(dirname "$0")/.."
(cd frontend && pnpm install --frozen-lockfile && pnpm build)
uv run uvicorn api.main:app --port 8000
