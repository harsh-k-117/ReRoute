"""replan/apply.py - apply a disruption: time-dependent travel, vehicle availability, orphaned parcels + rescue pickups

Lane : P2 Replan & quality lead (single writer for this path)
Stack: Python 3.12 · Pydantic v2 · pure + deterministic (seeded RNG, iteration budgets, ties by ID: D10) · tests: pytest · lint: ruff · snapshot(now) -> freeze -> apply -> repair/eject -> reinsert -> improve
Spec : D3, D4
"""
from __future__ import annotations
