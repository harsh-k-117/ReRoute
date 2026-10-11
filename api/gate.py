"""api/gate.py - server-enforced confirm gate: 409 without confirm, 422 on unknown place

Lane : P3 Integration & language lead (single writer for this path)
Stack: Python 3.12 · FastAPI · Pydantic v2 · uvicorn · mock mode serves fixtures · serves the built UI (frontend/dist)
Spec : D8, I9, I10
"""
from __future__ import annotations
