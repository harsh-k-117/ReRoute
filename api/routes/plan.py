"""api/routes/plan.py - POST /plan/initial

Lane : P3 Integration & language lead (single writer for this path)
Stack: Python 3.12 · FastAPI · Pydantic v2 · uvicorn · mock mode serves fixtures · serves the built UI (frontend/dist)
Spec : OpenAPI -> openapi-typescript
"""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/plan", tags=["plan"])

# TODO(P3): POST /plan/initial
