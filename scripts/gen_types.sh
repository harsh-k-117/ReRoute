#!/usr/bin/env bash
# scripts/gen_types.sh - FastAPI OpenAPI -> TypeScript types (UI and API cannot drift)
# Lane : P3 Integration & language lead
# Stack: bash + Python 3.12 (stdlib argparse) · uv · openapi-typescript
set -euo pipefail
cd "$(dirname "$0")/.."
uv run python -c "import json; from api.main import app; print(json.dumps(app.openapi()))" > frontend/openapi.json
(cd frontend && pnpm exec openapi-typescript openapi.json -o src/api/schema.d.ts)
