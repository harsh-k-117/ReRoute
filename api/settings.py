"""api/settings.py - env-driven settings (mock mode, LLM flag, transfer minutes)

Lane : P3 Integration & language lead (single writer for this path)
Stack: Python 3.12 · FastAPI · Pydantic v2 · uvicorn · mock mode serves fixtures · serves the built UI (frontend/dist)
Spec : mock mode
"""
from __future__ import annotations

import os

MOCK_MODE = os.getenv("REROUTE_MOCK", "0") == "1"
LLM_EXTRACTOR = os.getenv("REROUTE_LLM_EXTRACTOR", "0") == "1"
