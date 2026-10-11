"""Cheap rejection checks performed before route construction."""

from __future__ import annotations

from contract.models import Delivery, Reason, ReasonCode, Scenario

from .travel import travel_time


def prescreen_delivery(scenario: Scenario, delivery: Delivery) -> tuple[bool, list[Reason]]:
    locations = {location.id for location in scenario.locations}
    reasons: list[Reason] = []
    if delivery.location_id not in locations:
        reasons.append(
            Reason(
                code=ReasonCode.UNKNOWN_LOCATION,
                detail=f"Delivery {delivery.id} names unknown location {delivery.location_id}.",
            )
        )
        return False, reasons
    max_capacity = max((vehicle.capacity for vehicle in scenario.vehicles), default=0)
    if delivery.demand > max_capacity:
        reasons.append(
            Reason(
                code=ReasonCode.OVERSIZE,
                detail=(
                    f"Demand {delivery.demand} exceeds every vehicle capacity "
                    f"(maximum {max_capacity})."
                ),
            )
        )
    reachable = False
    for vehicle in scenario.vehicles:
        arrival = scenario.start_time + travel_time(
            scenario, (), vehicle.start_location_id, delivery.location_id, scenario.start_time
        )
        if arrival <= delivery.window_close and (
            vehicle.shift_end is None or arrival + delivery.service_time <= vehicle.shift_end
        ):
            reachable = True
            break
    if not reachable:
        reasons.append(
            Reason(
                code=ReasonCode.WINDOW_UNREACHABLE,
                detail=(
                    f"No vehicle can reach {delivery.location_id} by window close "
                    f"{delivery.window_close}."
                ),
            )
        )
    return not reasons, reasons
