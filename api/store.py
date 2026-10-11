"""api/store.py - session + plan-version store with undo

Lane : P3 Integration & language lead (single writer for this path)
Stack: Python 3.12 · FastAPI · Pydantic v2 · uvicorn · mock mode serves fixtures · serves the built UI (frontend/dist)
Spec : versions, undo
"""
from __future__ import annotations
