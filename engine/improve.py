"""engine/improve.py - ruin-and-recreate: remove a related cluster (10-25%), reinsert by regret, keep if better

Lane : P1 Algorithm lead (single writer for this path)
Stack: Python 3.12 · Pydantic v2 · pure + deterministic (seeded RNG, iteration budgets, ties by ID: D10) · tests: pytest · lint: ruff · custom solver: regret-2 insertion + ruin-and-recreate (no solver dependency; OR-Tools only in benchmarks)
Spec : D10
"""
from __future__ import annotations

from contract.models import Plan, Scenario


def improve(scenario: Scenario, plan: Plan, *, seed: int = 0, iterations: int = 200, free_suffix_only: bool = False) -> Plan:
    """Fixed iterations + seed => reproducible (I11)."""
    raise NotImplementedError
