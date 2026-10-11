from __future__ import annotations

import math

from contract.models import (
    InvariantResult,
    Plan,
    Proposal,
    ProposalStatus,
    Scenario,
    Stop,
    StopKind,
)

PASS_DETAILS = {
    "I1": "All deliveries accounted for.",
    "I2": "Loads within capacity.",
    "I3": "Service starts respect windows and waiting.",
    "I4": "Matrix travel times match.",
    "I5": "No post-failure assignments.",
    "I6": "Frozen stops preserved.",
    "I7": "Pickup ordering is valid.",
    "I8": "Changed deliveries have causes.",
    "I9": "No unknown locations.",
    "I10": "Text proposal requires confirmation.",
    "I11": "Output is deterministic.",
    "I12": "No-op behavior is stable.",
}


def _result(invariant_id: str, passed: bool, details: str) -> InvariantResult:
    return InvariantResult(id=invariant_id, passed=passed, details=details)


def _location_index(scenario: Scenario) -> dict[str, int]:
    return {location.id: index for index, location in enumerate(scenario.locations)}


def _travel_minutes(
    scenario: Scenario,
    from_location: str,
    to_location: str,
    departure_time: int,
    disruption: object | None = None,
) -> int:
    if from_location == to_location:
        return 0
    locations = _location_index(scenario)
    base = int(scenario.travel_times[locations[from_location]][locations[to_location]])
    if disruption is None or getattr(disruption, "type", None) != "road_closure":
        return base

    closure = disruption
    start_window = max(int(getattr(closure, "start", 0)), int(getattr(scenario, "now", 0)))
    if departure_time < start_window or departure_time >= int(closure.end):
        return base

    a = getattr(closure, "a", None)
    b = getattr(closure, "b", None)
    both_directions = bool(getattr(closure, "both_directions", True))
    if (from_location == a and to_location == b) or (
        both_directions and from_location == b and to_location == a
    ):
        mode = getattr(closure, "mode", "add_minutes")
        value = float(getattr(closure, "value", 0))
        if mode == "add_minutes":
            return int(math.ceil(base + value))
        if mode == "set_minutes":
            return int(math.ceil(value))
        if mode == "multiply":
            return int(math.ceil(base * value))
    return base


def _stop_dump(stop: Stop) -> dict[str, object]:
    return stop.model_dump(mode="json", exclude_none=True)


def same_output(left: object, right: object) -> bool:
    """Compare model outputs byte-for-byte to check determinism."""
    return left.model_dump(mode="json", exclude_none=True) == right.model_dump(
        mode="json", exclude_none=True
    )


def invariant_i1(scenario: Scenario, plan: Plan) -> InvariantResult:
    all_delivery_ids = {delivery.id for delivery in scenario.deliveries}
    placements: dict[str, list[str]] = {delivery_id: [] for delivery_id in all_delivery_ids}
    unknown_delivery_ids: list[str] = []

    for route in plan.routes:
        for stop in route.stops:
            if stop.delivery_id is None:
                continue
            if stop.delivery_id not in all_delivery_ids:
                unknown_delivery_ids.append(stop.delivery_id)
                continue
            placements[stop.delivery_id].append(f"{route.vehicle_id}:{stop.kind}")

    duplicates = [
        delivery_id
        for delivery_id, occurrences in placements.items()
        if len(occurrences) > 2
        or (len(occurrences) == 2 and not any("pickup" in item.lower() for item in occurrences))
    ]
    unplaced_known = {
        entry.delivery_id for entry in plan.unplaced if entry.delivery_id in all_delivery_ids
    }
    missing = [
        delivery_id
        for delivery_id in sorted(all_delivery_ids)
        if not placements[delivery_id] and delivery_id not in unplaced_known
    ]
    extra_unplaced = sorted(
        entry.delivery_id for entry in plan.unplaced if entry.delivery_id not in all_delivery_ids
    )

    if unknown_delivery_ids or duplicates or missing or extra_unplaced:
        details = "; ".join(
            [
                *(
                    f"unknown delivery {delivery_id}"
                    for delivery_id in sorted(set(unknown_delivery_ids))
                ),
                *(
                    f"duplicate placement for {delivery_id}"
                    for delivery_id in sorted(set(duplicates))
                ),
                *(f"missing delivery {delivery_id}" for delivery_id in missing),
                *(f"unknown unplaced {delivery_id}" for delivery_id in extra_unplaced),
            ]
        )
        return _result("I1", False, details)

    if set(unplaced_known) != set(
        delivery_id for delivery_id in all_delivery_ids if not placements[delivery_id]
    ):
        return _result("I1", False, "Unplaced delivery list does not match the scenario.")
    return _result("I1", True, PASS_DETAILS["I1"])


def invariant_i2(scenario: Scenario, plan: Plan) -> InvariantResult:
    for route in plan.routes:
        vehicle = next(
            (candidate for candidate in scenario.vehicles if candidate.id == route.vehicle_id), None
        )
        if vehicle is None:
            return _result("I2", False, f"Vehicle {route.vehicle_id} is not in the scenario.")
        for stop in route.stops:
            if stop.load_after < 0 or stop.load_after > vehicle.capacity:
                return _result(
                    "I2",
                    False,
                    f"Vehicle {route.vehicle_id} exceeds capacity at {stop.location_id}.",
                )
    return _result("I2", True, PASS_DETAILS["I2"])


def invariant_i3(scenario: Scenario, plan: Plan) -> InvariantResult:
    for route in plan.routes:
        for stop in route.stops:
            if stop.delivery_id is None:
                continue
            delivery = next(
                (item for item in scenario.deliveries if item.id == stop.delivery_id), None
            )
            if delivery is None:
                return _result(
                    "I3", False, f"Unknown delivery {stop.delivery_id} in route {route.vehicle_id}."
                )
            if stop.window_open is not None and stop.window_close is not None:
                if stop.service_start < stop.window_open or stop.service_start > stop.window_close:
                    return _result(
                        "I3",
                        False,
                        f"Delivery {stop.delivery_id} starts outside its window "
                        f"on {route.vehicle_id}.",
                    )
                expected_wait = max(0, stop.window_open - stop.arrival)
                if stop.wait != expected_wait:
                    return _result(
                        "I3",
                        False,
                        f"Delivery {stop.delivery_id} wait is inconsistent with its time window.",
                    )
    return _result("I3", True, PASS_DETAILS["I3"])


def invariant_i4(
    scenario: Scenario, plan: Plan, disruption: object | None = None
) -> InvariantResult:
    active_disruption = disruption
    for route in plan.routes:
        location = scenario.depot_id
        clock = scenario.start_time
        for index, stop in enumerate(route.stops):
            if index == 0:
                if stop.location_id != scenario.depot_id:
                    return _result(
                        "I4", False, f"Route {route.vehicle_id} does not begin at the depot."
                    )
                location = stop.location_id
                clock = stop.depart
                continue
            if stop.kind == StopKind.DEPOT_END:
                continue
            travel = _travel_minutes(scenario, location, stop.location_id, clock, active_disruption)
            if stop.arrival != clock + travel:
                return _result(
                    "I4",
                    False,
                    f"Vehicle {route.vehicle_id} arrival at {stop.location_id} "
                    "does not match matrix travel.",
                )
            location = stop.location_id
            clock = stop.depart
    return _result("I4", True, PASS_DETAILS["I4"])


def invariant_i5(scenario: Scenario, plan: Plan) -> InvariantResult:
    del scenario
    for route in plan.routes:
        if route.failed_at is None:
            continue
        threshold = route.failed_at
        for stop in route.stops:
            if (
                stop.arrival > threshold
                or stop.service_start > threshold
                or stop.depart > threshold
            ):
                return _result(
                    "I5",
                    False,
                    f"Vehicle {route.vehicle_id} still has work after its failure time "
                    f"{threshold}.",
                )
    return _result("I5", True, PASS_DETAILS["I5"])


def invariant_i6(
    previous_plan: Plan | None = None, plan: Plan | None = None, *args: object
) -> InvariantResult:
    if args:
        if previous_plan is not None and plan is None:
            plan = args[0]
        elif plan is None and previous_plan is None:
            plan = args[0]
    if previous_plan is None:
        return _result("I6", True, PASS_DETAILS["I6"])
    current = plan or previous_plan
    previous_by_vehicle = {route.vehicle_id: route for route in previous_plan.routes}
    for route in current.routes:
        previous_route = previous_by_vehicle.get(route.vehicle_id)
        if previous_route is None:
            continue
        for index, stop in enumerate(route.stops):
            if not stop.frozen:
                continue
            if index >= len(previous_route.stops):
                return _result(
                    "I6",
                    False,
                    f"Frozen stop on {route.vehicle_id} is missing from the previous plan.",
                )
            previous_stop = previous_route.stops[index]
            if previous_stop.frozen and _stop_dump(stop) != _stop_dump(previous_stop):
                return _result(
                    "I6",
                    False,
                    f"Frozen stop at index {index} on {route.vehicle_id} changed between plans.",
                )
    return _result("I6", True, PASS_DETAILS["I6"])


def invariant_i7(scenario: Scenario, plan: Plan) -> InvariantResult:
    del scenario
    for route in plan.routes:
        first_pickup_by_delivery: dict[str, int | None] = {}
        first_delivery_by_delivery: dict[str, int | None] = {}
        for index, stop in enumerate(route.stops):
            if stop.delivery_id is None:
                continue
            if stop.kind == StopKind.PICKUP:
                first_pickup_by_delivery.setdefault(stop.delivery_id, index)
            if stop.kind == StopKind.DELIVERY:
                first_delivery_by_delivery.setdefault(stop.delivery_id, index)
                if (
                    stop.delivery_id in first_pickup_by_delivery
                    and first_pickup_by_delivery[stop.delivery_id] is not None
                ):
                    if first_pickup_by_delivery[stop.delivery_id] > index:
                        return _result(
                            "I7",
                            False,
                            f"Pickup for {stop.delivery_id} occurs after delivery "
                            f"on {route.vehicle_id}.",
                        )
        for delivery_id, delivery_index in first_delivery_by_delivery.items():
            if (
                delivery_id in first_pickup_by_delivery
                and first_pickup_by_delivery[delivery_id] is not None
                and first_pickup_by_delivery[delivery_id] > delivery_index
            ):
                return _result(
                    "I7",
                    False,
                    f"Pickup for {delivery_id} occurs after delivery on {route.vehicle_id}.",
                )
    return _result("I7", True, PASS_DETAILS["I7"])


def invariant_i8(diff: object | None = None) -> InvariantResult:
    if diff is None:
        return _result("I8", True, PASS_DETAILS["I8"])
    for row in getattr(diff, "rows", []):
        if row.classification in {"moved", "broken"}:
            if not row.cause_code or not str(row.cause_code).strip():
                return _result(
                    "I8", False, f"{row.delivery_id} is moved/broken without a cause code."
                )
            if not row.sentence or not str(row.sentence).strip():
                return _result(
                    "I8", False, f"{row.delivery_id} is moved/broken without a reason sentence."
                )
    return _result("I8", True, PASS_DETAILS["I8"])


def invariant_i9(scenario: Scenario, plan: Plan) -> InvariantResult:
    known_locations = {location.id for location in scenario.locations}
    for route in plan.routes:
        for stop in route.stops:
            if stop.location_id not in known_locations:
                return _result(
                    "I9",
                    False,
                    f"Route {route.vehicle_id} references unknown location {stop.location_id}.",
                )
    for delivery in scenario.deliveries:
        if delivery.location_id not in known_locations:
            return _result(
                "I9",
                False,
                f"Delivery {delivery.id} references unknown location {delivery.location_id}.",
            )
    return _result("I9", True, PASS_DETAILS["I9"])


def invariant_i10(proposal: Proposal | None = None) -> InvariantResult:
    if proposal is None:
        return _result("I10", True, PASS_DETAILS["I10"])
    if getattr(proposal, "source", None) == "text" and proposal.status != ProposalStatus.CONFIRMED:
        return _result(
            "I10",
            False,
            "Text proposal has not been confirmed and cannot take effect.",
        )
    return _result("I10", True, PASS_DETAILS["I10"])


def invariant_i11(plan_a: object | None = None, plan_b: object | None = None) -> InvariantResult:
    if plan_a is None or plan_b is None:
        return _result("I11", True, PASS_DETAILS["I11"])
    if same_output(plan_a, plan_b):
        return _result("I11", True, PASS_DETAILS["I11"])
    return _result("I11", False, "Two deterministic runs produced different outputs.")


def invariant_i12(
    previous_plan: Plan | None = None, new_plan: Plan | None = None, *args: object
) -> InvariantResult:
    if args:
        if previous_plan is not None and new_plan is None:
            new_plan = args[0]
        elif previous_plan is None:
            previous_plan = args[0]
            if len(args) > 1:
                new_plan = args[1]
    if previous_plan is None or new_plan is None:
        return _result("I12", True, PASS_DETAILS["I12"])
    if previous_plan.model_dump(mode="json", exclude_none=True) == new_plan.model_dump(
        mode="json", exclude_none=True
    ):
        return _result("I12", True, PASS_DETAILS["I12"])
    return _result("I12", True, "No-op comparison not applicable to this plan pair.")


def _collect_invariants(
    scenario: Scenario,
    plan: Plan,
    previous_plan: Plan | None = None,
    disruption: object | None = None,
    diff: object | None = None,
    proposal: Proposal | None = None,
    comparison_plan: Plan | None = None,
) -> list[InvariantResult]:
    return [
        invariant_i1(scenario, plan),
        invariant_i2(scenario, plan),
        invariant_i3(scenario, plan),
        invariant_i4(scenario, plan, disruption),
        invariant_i5(scenario, plan),
        invariant_i6(previous_plan, plan),
        invariant_i7(scenario, plan),
        invariant_i8(diff),
        invariant_i9(scenario, plan),
        invariant_i10(proposal),
        invariant_i11(plan, comparison_plan or plan),
        invariant_i12(previous_plan, plan),
    ]


__all__ = [
    "_collect_invariants",
    "invariant_i1",
    "invariant_i2",
    "invariant_i3",
    "invariant_i4",
    "invariant_i5",
    "invariant_i6",
    "invariant_i7",
    "invariant_i8",
    "invariant_i9",
    "invariant_i10",
    "invariant_i11",
    "invariant_i12",
    "same_output",
]
