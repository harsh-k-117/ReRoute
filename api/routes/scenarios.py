"""api/routes/scenarios.py - GET /scenarios, GET /scenarios/{name}

Lane : P3 Integration & language lead (single writer for this path)
Stack: Python 3.12 · FastAPI · Pydantic v2 · uvicorn · mock mode serves fixtures · serves the built UI (frontend/dist)
Spec : OpenAPI -> openapi-typescript
"""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/scenarios", tags=["scenarios"])

# TODO(P3): GET /scenarios, GET /scenarios/{name}
