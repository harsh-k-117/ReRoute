"""replan/ledger.py - reason ledger: completed | vehicle_failed | closure_delay | displaced_by_urgent | knock_on | no_feasible_slot

Lane : P2 Replan & quality lead (single writer for this path)
Stack: Python 3.12 · Pydantic v2 · pure + deterministic (seeded RNG, iteration budgets, ties by ID: D10) · tests: pytest · lint: ruff · snapshot(now) -> freeze -> apply -> repair/eject -> reinsert -> improve
Spec : I8
"""
from __future__ import annotations
