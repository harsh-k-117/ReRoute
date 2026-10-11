"""api/routes/state.py - GET /state (current plan version, vehicle states at `now`)

Lane : P3 Integration & language lead (single writer for this path)
Stack: Python 3.12 · FastAPI · Pydantic v2 · uvicorn · mock mode serves fixtures · serves the built UI (frontend/dist)
Spec : OpenAPI -> openapi-typescript
"""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/state", tags=["state"])

# TODO(P3): GET /state (current plan version, vehicle states at `now`)
