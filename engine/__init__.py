"""Public engine interfaces (implementation lives in the engine lane)."""

from contract.signatures import (
    build_plan,
    diagnose_unplaced,
    improve,
    insert_deliveries,
    simulate_route,
)

__all__ = ["build_plan", "diagnose_unplaced", "improve", "insert_deliveries", "simulate_route"]
