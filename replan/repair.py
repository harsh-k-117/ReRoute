"""replan/repair.py - re-simulate free suffixes with windows softened, fix locally, eject remaining violators

Lane : P2 Replan & quality lead (single writer for this path)
Stack: Python 3.12 · Pydantic v2 · pure + deterministic (seeded RNG, iteration budgets, ties by ID: D10) · tests: pytest · lint: ruff · snapshot(now) -> freeze -> apply -> repair/eject -> reinsert -> improve
Spec : I5, I8
"""
from __future__ import annotations
