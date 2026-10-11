"""api/mock.py - mock mode: serve golden fixtures from every endpoint so UI never waits for the engine

Lane : P3 Integration & language lead (single writer for this path)
Stack: Python 3.12 · FastAPI · Pydantic v2 · uvicorn · mock mode serves fixtures · serves the built UI (frontend/dist)
Spec : fixtures first
"""
from __future__ import annotations
