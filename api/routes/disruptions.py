"""api/routes/disruptions.py - POST /disruptions/preview, POST /disruptions/interpret

Lane : P3 Integration & language lead (single writer for this path)
Stack: Python 3.12 · FastAPI · Pydantic v2 · uvicorn · mock mode serves fixtures · serves the built UI (frontend/dist)
Spec : OpenAPI -> openapi-typescript
"""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/disruptions", tags=["disruptions"])

# TODO(P3): POST /disruptions/preview, POST /disruptions/interpret
