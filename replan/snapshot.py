"""Current-state snapshots used by disruption repair."""

from contract.models import Plan, PlanSnapshot, Scenario, VehicleReadyState


def snapshot(scenario: Scenario, plan: Plan, now: int) -> PlanSnapshot:
    vehicles: list[VehicleReadyState] = []
    for vehicle in scenario.vehicles:
        route = next(route for route in plan.routes if route.vehicle_id == vehicle.id)
        frozen = [
            stop.model_copy(update={"frozen": True}) for stop in route.stops if stop.depart <= now
        ]
        last = frozen[-1] if frozen else None
        vehicles.append(
            VehicleReadyState(
                vehicle_id=vehicle.id,
                frozen_stops=frozen,
                ready_location_id=last.location_id if last else vehicle.start_location_id,
                ready_time=last.depart if last else scenario.start_time,
                onboard_load=last.load_after if last else 0,
            )
        )
    return PlanSnapshot(plan_ref=plan.version_id, now=now, vehicles=vehicles)
