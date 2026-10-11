"""diff/classify.py - classify(): kept (same vehicle, ETA within +-5) / moved / broken, reading the reason ledger

Lane : P2 Replan & quality lead (single writer for this path)
Stack: Python 3.12 · Pydantic v2 · pure + deterministic (seeded RNG, iteration budgets, ties by ID: D10) · tests: pytest · lint: ruff · reason ledger -> kept / moved / broken
Spec : D7, I8
"""
from __future__ import annotations

from contract.models import Diff, Plan


def classify(old: Plan, new: Plan, ledger: list[dict]) -> Diff:
    raise NotImplementedError
