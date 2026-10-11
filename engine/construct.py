"""engine/construct.py - build_plan + insert_deliveries: parallel regret-2 insertion with cached best insertions

Lane : P1 Algorithm lead (single writer for this path)
Stack: Python 3.12 · Pydantic v2 · pure + deterministic (seeded RNG, iteration budgets, ties by ID: D10) · tests: pytest · lint: ruff · custom solver: regret-2 insertion + ruin-and-recreate (no solver dependency; OR-Tools only in benchmarks)
Spec : D2, D3
"""
from __future__ import annotations

from contract.models import Plan, PlanState, Scenario


def build_plan(scenario: Scenario, *, seed: int = 0) -> Plan:
    """Pre-screen -> regret-2 insertion -> improve()."""
    raise NotImplementedError


def insert_deliveries(state: PlanState, pool: list[str], objective, *, scenario: Scenario) -> Plan:
    """Works on frozen prefixes, ready states and pickup stops. Used by build_plan AND replan."""
    raise NotImplementedError
