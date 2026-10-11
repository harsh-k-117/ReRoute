"""engine/diagnose.py - diagnose_unplaced: per-vehicle binding constraint + 'what would it take' hint (star)

Lane : P1 Algorithm lead (single writer for this path)
Stack: Python 3.12 · Pydantic v2 · pure + deterministic (seeded RNG, iteration budgets, ties by ID: D10) · tests: pytest · lint: ruff · custom solver: regret-2 insertion + ruin-and-recreate (no solver dependency; OR-Tools only in benchmarks)
Spec : D9
"""
from __future__ import annotations

from contract.models import Plan, Scenario, Unplaced


def diagnose_unplaced(scenario: Scenario, plan: Plan) -> list[Unplaced]:
    """Reason codes: oversize | window_unreachable | no_capacity_at_stop_k | pushes_stop_x_late | no_vehicle_available."""
    raise NotImplementedError
