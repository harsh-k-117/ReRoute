"""Scale-up scenarios for deterministic engine and validator profiling."""

from __future__ import annotations

from contract.models import Scenario

from .city import generate_city


def generate_stress(
    seed: int,
    n_deliveries: int = 100,
    n_vehicles: int = 10,
) -> Scenario:
    """Generate a deterministic workload, up to the project's 200x15 target."""
    if not 1 <= n_deliveries <= 200:
        raise ValueError("n_deliveries must be between 1 and 200")
    if not 1 <= n_vehicles <= 15:
        raise ValueError("n_vehicles must be between 1 and 15")
    scenario = generate_city(
        seed=seed,
        n_deliveries=n_deliveries,
        n_vehicles=n_vehicles,
        include_impossible=False,
    )
    return scenario.model_copy(update={"name": f"stress-{n_deliveries}x{n_vehicles}"})


__all__ = ["generate_stress"]
