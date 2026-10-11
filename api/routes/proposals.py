"""api/routes/proposals.py - POST /proposals/{id}/confirm, POST /proposals/{id}/discard (gate enforced server-side)

Lane : P3 Integration & language lead (single writer for this path)
Stack: Python 3.12 · FastAPI · Pydantic v2 · uvicorn · mock mode serves fixtures · serves the built UI (frontend/dist)
Spec : OpenAPI -> openapi-typescript
"""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/proposals", tags=["proposals"])

# TODO(P3): POST /proposals/{id}/confirm, POST /proposals/{id}/discard (gate enforced server-side)
