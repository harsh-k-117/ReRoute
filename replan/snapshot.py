"""replan/snapshot.py - snapshot(plan, now): frozen prefix, ready location/time, on-board load, breakdown site

Lane : P2 Replan & quality lead (single writer for this path)
Stack: Python 3.12 · Pydantic v2 · pure + deterministic (seeded RNG, iteration budgets, ties by ID: D10) · tests: pytest · lint: ruff · snapshot(now) -> freeze -> apply -> repair/eject -> reinsert -> improve
Spec : D5, I6
"""
from __future__ import annotations

from contract.models import Disruption, Plan, PlanState, Scenario


def snapshot(scenario: Scenario, plan: Plan, now: int, disruptions: list[Disruption] | None = None) -> PlanState:
    """Fixed = service ended <= now, in progress, or vehicle already driving to it (D5)."""
    raise NotImplementedError
