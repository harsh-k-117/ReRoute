"""Deterministic bounded ruin-and-recreate improvement."""

from __future__ import annotations

from contract.models import Plan, Scenario

from .construct import insert_deliveries
from .objective import score


def improve(scenario: Scenario, plan: Plan, iterations: int = 0, seed: int | None = None) -> Plan:
    """Try deterministic single-delivery ruin-and-recreate neighborhoods."""
    del seed
    best = plan
    for _ in range(max(0, iterations)):
        changed = False
        delivery_ids = sorted(
            stop.delivery_id
            for route in best.routes
            for stop in route.stops
            if stop.delivery_id
        )
        for delivery_id in delivery_ids:
            delivery = next(item for item in scenario.deliveries if item.id == delivery_id)
            routes = []
            removed = False
            for route in best.routes:
                stops = [
                    stop for stop in route.stops
                    if stop.delivery_id != delivery_id
                ]
                if len(stops) != len(route.stops):
                    removed = True
                routes.append(route.model_copy(update={"stops": stops}))
            if not removed:
                continue
            candidate = insert_deliveries(
                scenario,
                best.model_copy(update={"routes": routes}),
                [delivery],
            )
            if not candidate.unplaced and score(candidate) < score(best):
                best = candidate
                changed = True
                break
        if not changed:
            break
    return best
