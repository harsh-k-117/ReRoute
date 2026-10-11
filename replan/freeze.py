"""replan/freeze.py - freeze rule helpers (D5); frozen stops must be byte-identical (I6)

Lane : P2 Replan & quality lead (single writer for this path)
Stack: Python 3.12 · Pydantic v2 · pure + deterministic (seeded RNG, iteration budgets, ties by ID: D10) · tests: pytest · lint: ruff · snapshot(now) -> freeze -> apply -> repair/eject -> reinsert -> improve
Spec : D5, I6
"""
from __future__ import annotations
