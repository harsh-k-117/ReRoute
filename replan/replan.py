"""replan/replan.py - replan(): one entry point for closure, vehicle failure, urgent delivery

Lane : P2 Replan & quality lead (single writer for this path)
Stack: Python 3.12 · Pydantic v2 · pure + deterministic (seeded RNG, iteration budgets, ties by ID: D10) · tests: pytest · lint: ruff · snapshot(now) -> freeze -> apply -> repair/eject -> reinsert -> improve
Spec : D5-D9, I5, I6, I12
"""
from __future__ import annotations

from contract.models import Disruption, Plan, ReplanResult, Scenario


def replan(scenario: Scenario, plan: Plan, disruption: Disruption, now: int, *, seed: int = 0) -> ReplanResult:
    """snapshot -> freeze -> apply -> repair/eject -> reinsert (stability-weighted) -> short improve on free suffixes
    -> verify gate. If the validator fails the replan is DISCARDED (never show a bad plan)."""
    raise NotImplementedError
