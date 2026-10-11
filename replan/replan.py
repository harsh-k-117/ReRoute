"""Disruption pipeline: snapshot, freeze, rebuild, validate, and diff."""

from contract.models import (
    Plan,
    Reason,
    ReasonCode,
    ReplanResult,
    RoadClosure,
    Scenario,
    Stop,
    StopKind,
    Unplaced,
    UrgentDelivery,
    VehicleFailure,
)
from diff.classify import classify
from engine.construct import build_plan
from engine.simulate import simulate_route
from verify.validator import validate


def _remaining_scenario(scenario: Scenario, completed: set[str]) -> Scenario:
    return scenario.model_copy(
        update={
            "deliveries": [
                delivery for delivery in scenario.deliveries if delivery.id not in completed
            ]
        }
    )


def _failure_replan(scenario: Scenario, plan: Plan, event: VehicleFailure) -> Plan:
    failed_route = next(route for route in plan.routes if route.vehicle_id == event.vehicle_id)
    frozen = [stop for stop in failed_route.stops if stop.depart <= event.at_time]
    future_ids = {
        stop.delivery_id
        for stop in failed_route.stops
        if stop.delivery_id is not None and stop.depart > event.at_time
    }
    routes = [route for route in plan.routes if route.vehicle_id != event.vehicle_id]
    for delivery in (delivery for delivery in scenario.deliveries if delivery.id in future_ids):
        choices = []
        for route in routes:
            existing = [stop for stop in route.stops if stop.kind != StopKind.DEPOT_START]
            for position in range(len(existing) + 1):
                pickup_location = (
                    existing[position - 1].location_id if position else scenario.depot_id
                )
                inserted = (
                    existing[:position]
                    + [
                        Stop(
                            kind=StopKind.PICKUP,
                            delivery_id=delivery.id,
                            parcel_ids=[delivery.id],
                            location_id=pickup_location,
                            arrival=scenario.start_time,
                            service_start=scenario.start_time,
                            depart=scenario.start_time,
                            load_after=0,
                        ),
                        Stop(
                            kind=StopKind.DELIVERY,
                            delivery_id=delivery.id,
                            location_id=delivery.location_id,
                            arrival=scenario.start_time,
                            service_start=scenario.start_time,
                            depart=scenario.start_time,
                            load_after=0,
                        ),
                    ]
                    + existing[position:]
                )
                candidate = simulate_route(
                    scenario,
                    route.vehicle_id,
                    [route.stops[0], *inserted],
                    start_load=route.stops[0].load_after,
                )
                if not candidate.violations:
                    choices.append(
                        (
                            candidate.total_travel + candidate.total_wait,
                            route.vehicle_id,
                            candidate,
                        )
                    )
        if choices:
            _, vehicle_id, selected = min(choices, key=lambda item: item[:2])
            routes = [selected if route.vehicle_id == vehicle_id else route for route in routes]
    repaired = plan.model_copy(update={"routes": routes, "unplaced": []})
    routes.append(failed_route.model_copy(update={"stops": frozen, "failed_at": event.at_time}))
    return repaired.model_copy(
        update={
            "routes": sorted(routes, key=lambda route: route.vehicle_id),
            "version_id": f"{plan.version_id}-failure-{event.vehicle_id}-{event.at_time}",
            "scenario_ref": scenario.name,
            "unplaced": repaired.unplaced,
        }
    )


def _urgent_replan(scenario: Scenario, plan: Plan, event: UrgentDelivery) -> Plan:
    urgent = event.delivery
    augmented = scenario.model_copy(update={"deliveries": [*scenario.deliveries, urgent]})
    best: tuple[int, str, Plan] | None = None
    for route in plan.routes:
        pickup = Stop(
            kind=StopKind.PICKUP,
            delivery_id=urgent.id,
            parcel_ids=[urgent.id],
            location_id=scenario.depot_id,
            arrival=event.report_time,
            service_start=event.report_time,
            depart=event.report_time,
            load_after=0,
            badges=["NEW"],
        )
        delivery = Stop(
            kind=StopKind.DELIVERY,
            delivery_id=urgent.id,
            location_id=urgent.location_id,
            arrival=event.report_time,
            service_start=event.report_time,
            depart=event.report_time,
            load_after=0,
            badges=["NEW"],
        )
        stops = [*route.stops, pickup, delivery]
        candidate = simulate_route(
            augmented,
            route.vehicle_id,
            stops,
            start_time=scenario.start_time,
            release_times={urgent.id: max(event.report_time, urgent.release_time or 0)},
        )
        if not candidate.violations:
            cost = candidate.total_travel + candidate.total_wait
            result = plan.model_copy(
                update={
                    "routes": [
                        candidate if current.vehicle_id == route.vehicle_id else current
                        for current in plan.routes
                    ],
                    "version_id": f"{plan.version_id}-urgent-{urgent.id}",
                    "scenario_ref": augmented.name,
                }
            )
            if best is None or (cost, route.vehicle_id) < (best[0], best[1]):
                best = (cost, route.vehicle_id, result)
    if best is not None:
        return best[2]
    return plan.model_copy(
        update={
            "version_id": f"{plan.version_id}-urgent-{urgent.id}",
            "unplaced": [
                *plan.unplaced,
                Unplaced(
                    delivery_id=urgent.id,
                    reasons=[
                        Reason(
                            code=ReasonCode.NO_FEASIBLE_SLOT,
                            detail=(
                                "No vehicle can insert the urgent delivery without "
                                "violating capacity or its window."
                            ),
                        )
                    ],
                ),
            ],
        }
    )


def replan(scenario: Scenario, plan: Plan, disruption: object) -> ReplanResult:
    if isinstance(disruption, RoadClosure):
        affected = False
        for route in plan.routes:
            previous = scenario.depot_id
            for stop in route.stops:
                if disruption.start <= stop.depart < disruption.end and (
                    (previous == disruption.a and stop.location_id == disruption.b)
                    or (
                        disruption.both_directions
                        and previous == disruption.b
                        and stop.location_id == disruption.a
                    )
                ):
                    affected = True
                previous = stop.location_id
        revised = (
            build_plan(scenario, closures=[disruption])
            if affected
            else plan.model_copy(update={"version_id": f"{plan.version_id}-closure-noop"})
        )
    elif isinstance(disruption, VehicleFailure):
        revised = _failure_replan(scenario, plan, disruption)
    elif isinstance(disruption, UrgentDelivery):
        revised = _urgent_replan(scenario, plan, disruption)
    else:
        raise TypeError(f"unsupported disruption: {type(disruption).__name__}")
    diff = classify(plan, revised)
    report = validate(scenario, revised, previous_plan=plan, disruption=disruption, diff=diff)
    return ReplanResult(
        plan=revised,
        previous_plan_ref=plan.version_id,
        diff=diff,
        validation_report=report,
        trace=[f"Applied {disruption.type}"],
    )
