"""Lexicographic plan scoring used by construction and improvement."""

from __future__ import annotations

from contract.models import Plan


def score(
    plan: Plan,
    baseline_plan: Plan | None = None,
    stability_weight: int = 0,
) -> tuple[int, int, int, str]:
    broken = len(plan.unplaced)
    moved = 0
    if baseline_plan is not None:
        before = {
            stop.delivery_id: (route.vehicle_id, stop.service_start)
            for route in baseline_plan.routes
            for stop in route.stops
            if stop.delivery_id
        }
        for route in plan.routes:
            for stop in route.stops:
                if stop.delivery_id and stop.delivery_id in before:
                    old_vehicle, old_eta = before[stop.delivery_id]
                    if old_vehicle != route.vehicle_id or abs(old_eta - stop.service_start) > 5:
                        moved += 1
    effort = sum(route.total_travel + route.total_wait for route in plan.routes)
    effort += stability_weight * moved
    ids = ",".join(
        sorted(
            stop.delivery_id for route in plan.routes for stop in route.stops if stop.delivery_id
        )
    )
    return (broken, moved, effort, ids)
