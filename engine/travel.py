"""engine/travel.py - time-dependent travel function over the matrix + closure rule (D4)

Lane : P1 Algorithm lead (single writer for this path)
Stack: Python 3.12 · Pydantic v2 · pure + deterministic (seeded RNG, iteration budgets, ties by ID: D10) · tests: pytest · lint: ruff · custom solver: regret-2 insertion + ruin-and-recreate (no solver dependency; OR-Tools only in benchmarks)
Spec : D1, D4, I4
"""
from __future__ import annotations

from contract.models import RoadClosure, Scenario


def make_travel_fn(scenario: Scenario, closures: list[RoadClosure] | None = None):
    """Return travel(from, to, depart_time) -> minutes. Matrix entries are direct times (D4)."""
    raise NotImplementedError
