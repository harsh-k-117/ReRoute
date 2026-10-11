"""Human-readable feasibility diagnostics for deliveries."""

from __future__ import annotations

from contract.models import Delivery, Reason, ReasonCode, Scenario

from .prescreen import prescreen_delivery
from .travel import travel_time


def diagnose_unplaced(scenario: Scenario, delivery: Delivery) -> list[Reason]:
    feasible, reasons = prescreen_delivery(scenario, delivery)
    if not feasible:
        return reasons
    diagnostics: list[Reason] = []
    for vehicle in scenario.vehicles:
        arrival = scenario.start_time + travel_time(
            scenario, (), vehicle.start_location_id, delivery.location_id, scenario.start_time
        )
        if vehicle.capacity < delivery.demand:
            diagnostics.append(
                Reason(
                    code=ReasonCode.NO_CAPACITY_AT_STOP,
                    vehicle_id=vehicle.id,
                    detail=(
                        f"{vehicle.name} has capacity {vehicle.capacity}, below "
                        f"demand {delivery.demand}."
                    ),
                )
            )
        elif arrival > delivery.window_close:
            diagnostics.append(
                Reason(
                    code=ReasonCode.PUSHES_STOP_LATE,
                    vehicle_id=vehicle.id,
                    detail=(
                        f"{vehicle.name} reaches {delivery.location_id} after its window closes."
                    ),
                )
            )
        else:
            diagnostics.append(
                Reason(
                    code=ReasonCode.NO_FEASIBLE_SLOT,
                    vehicle_id=vehicle.id,
                    detail=f"No feasible insertion slot was found on {vehicle.name}.",
                )
            )
    return diagnostics or [
        Reason(
            code=ReasonCode.NO_VEHICLE_AVAILABLE,
            detail="No vehicle is available for this delivery.",
        )
    ]
