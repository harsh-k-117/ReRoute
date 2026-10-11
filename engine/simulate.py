"""Single source of truth for route timing, loads, and violations.

The simulator advances over direct matrix edges, applies active closures,
waits for windows and releases, and updates load after each service. Frozen
stops are passed through byte-for-byte and the returned Route records all
computed values plus violations.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from contract.models import Route, Scenario, Stop, StopKind

from .travel import travel_time


def simulate_route(
    scenario: Scenario,
    vehicle_id: str,
    stops: Sequence[Stop],
    start_location: str | None = None,
    start_time: int | None = None,
    start_load: int | None = None,
    closures: Sequence = (),
    release_times: Mapping[str, int] | None = None,
) -> Route:
    vehicle = next((item for item in scenario.vehicles if item.id == vehicle_id), None)
    if vehicle is None:
        raise ValueError(f"unknown vehicle {vehicle_id!r}")
    deliveries = {delivery.id: delivery for delivery in scenario.deliveries}
    ordered = list(stops)
    for stop in ordered:
        if stop.delivery_id is not None and stop.delivery_id not in deliveries:
            raise ValueError(f"route references unknown delivery {stop.delivery_id!r}")

    location = start_location or vehicle.start_location_id
    clock = scenario.start_time if start_time is None else start_time
    release_times = release_times or {}
    if start_load is None:
        start_load = sum(
            deliveries[stop.delivery_id].demand
            for stop in ordered
            if stop.delivery_id is not None and stop.kind != StopKind.PICKUP
        )
    load = start_load
    violations: list[str] = []
    if load < 0 or load > vehicle.capacity:
        violations.append(f"over capacity at route start: {load} > {vehicle.capacity}")

    result: list[Stop] = []
    total_travel = 0
    total_wait = 0
    delivered: set[str] = set()

    for original in ordered:
        if original.frozen:
            result.append(original)
            location, clock, load = original.location_id, original.depart, original.load_after
            continue
        if original.kind == StopKind.DEPOT_START:
            computed = original.model_copy(
                update={
                    "arrival": clock,
                    "service_start": clock,
                    "depart": clock,
                    "load_after": load,
                }
            )
            result.append(computed)
            location = original.location_id
            continue

        delivery = deliveries.get(original.delivery_id) if original.delivery_id else None
        if delivery is None and original.kind != StopKind.DEPOT_END:
            raise ValueError("delivery stop must identify a delivery")
        travel = travel_time(scenario, closures, location, original.location_id, clock)
        arrival = clock + travel
        total_travel += travel
        window_open = delivery.window_open if delivery else None
        window_close = delivery.window_close if delivery else None
        release = release_times.get(
            original.delivery_id or "", delivery.release_time if delivery else None
        )
        service_start = max(arrival, window_open or arrival, release or arrival)
        wait = service_start - arrival
        depart = service_start + (delivery.service_time if delivery else 0)
        if window_close is not None and service_start > window_close:
            violations.append(
                f"{original.delivery_id} starts after window close by "
                f"{service_start - window_close} minutes"
            )
        if delivery is not None:
            if original.kind == StopKind.PICKUP:
                if delivery.id in delivered:
                    violations.append(f"pickup after delivery: {delivery.id}")
                load += delivery.demand
            elif original.kind == StopKind.DELIVERY:
                load -= delivery.demand
                delivered.add(delivery.id)
        if load < 0:
            violations.append(f"negative load after {original.delivery_id}")
        if load > vehicle.capacity:
            violations.append(
                f"over capacity after {original.delivery_id}: {load} > {vehicle.capacity}"
            )
        if vehicle.shift_end is not None and depart > vehicle.shift_end:
            violations.append(f"shift end exceeded by {depart - vehicle.shift_end} minutes")
        result.append(original.model_copy(update={
            "arrival": arrival,
            "wait": wait,
            "service_start": service_start,
            "depart": depart,
            "load_after": load,
            "window_open": window_open,
            "window_close": window_close,
        }))
        total_wait += wait
        location, clock = original.location_id, depart

    if scenario.config.return_to_depot and result and location != scenario.depot_id:
        travel = travel_time(scenario, closures, location, scenario.depot_id, clock)
        arrival = clock + travel
        total_travel += travel
        result.append(Stop(
            kind=StopKind.DEPOT_END,
            location_id=scenario.depot_id,
            arrival=arrival,
            service_start=arrival,
            depart=arrival,
            load_after=load,
        ))
        if vehicle.shift_end is not None and arrival > vehicle.shift_end:
            violations.append(f"shift end exceeded by {arrival - vehicle.shift_end} minutes")

    return Route(
        vehicle_id=vehicle_id,
        stops=result,
        total_travel=total_travel,
        total_wait=total_wait,
        violations=violations,
    )
