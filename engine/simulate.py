"""engine/simulate.py - simulate_route: ONE source of truth for arrival, wait, start, depart, load-after, violations

Lane : P1 Algorithm lead (single writer for this path)
Stack: Python 3.12 · Pydantic v2 · pure + deterministic (seeded RNG, iteration budgets, ties by ID: D10) · tests: pytest · lint: ruff · custom solver: regret-2 insertion + ruin-and-recreate (no solver dependency; OR-Tools only in benchmarks)
Spec : D2, D3, I2, I3
"""
from __future__ import annotations

from contract.models import Route, RouteSim, Scenario
from contract.signatures import TravelFn


def simulate_route(
    scenario: Scenario,
    route: Route,
    *,
    start_time: int = 0,
    start_location: str | None = None,
    start_load: int | None = None,
    travel: TravelFn | None = None,
) -> RouteSim:
    """Forward-simulate one route. start = max(arrival, open); depart = start + service (D2).
    Load is checked at the start and after every pickup (D3 / I2)."""
    raise NotImplementedError
