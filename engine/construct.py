"""Deterministic regret-2 insertion construction.

1. Prescreen impossible deliveries.
2. Evaluate every delivery/vehicle/position with the simulator.
3. Insert the delivery with greatest regret (best versus second-best cost).
4. Break ties by delivery ID, vehicle ID, and position; no wall-clock choices.
"""

from __future__ import annotations

from collections.abc import Sequence

from contract.models import Delivery, Plan, Route, Scenario, Stop, StopKind, Unplaced

from .diagnose import diagnose_unplaced
from .prescreen import prescreen_delivery
from .simulate import simulate_route


def _empty_stop(scenario: Scenario) -> Stop:
    return Stop(
        kind=StopKind.DEPOT_START,
        location_id=scenario.depot_id,
        arrival=scenario.start_time,
        service_start=scenario.start_time,
        depart=scenario.start_time,
        load_after=0,
    )


def _candidate(
    scenario: Scenario,
    vehicle_id: str,
    deliveries: Sequence[Delivery],
    closures: Sequence = (),
) -> Route | None:
    stops = [_empty_stop(scenario)]
    stops.extend(
        Stop(
            kind=StopKind.DELIVERY,
            delivery_id=delivery.id,
            location_id=delivery.location_id,
            arrival=scenario.start_time,
            service_start=scenario.start_time,
            depart=scenario.start_time,
            load_after=0,
        )
        for delivery in deliveries
    )
    route = simulate_route(scenario, vehicle_id, stops, closures=closures)
    return route if not route.violations else None


def _route_with_insert(
    scenario: Scenario,
    route: Route,
    delivery: Delivery,
    position: int,
    closures: Sequence = (),
) -> Route | None:
    existing = [stop for stop in route.stops if stop.kind != StopKind.DEPOT_START]
    inserted = (
        existing[:position]
        + [
            Stop(
                kind=StopKind.DELIVERY,
                delivery_id=delivery.id,
                location_id=delivery.location_id,
                arrival=scenario.start_time,
                service_start=scenario.start_time,
                depart=scenario.start_time,
                load_after=0,
            )
        ]
        + existing[position:]
    )
    deliveries = [
        next(item for item in scenario.deliveries if item.id == stop.delivery_id)
        for stop in inserted
    ]
    return _candidate(scenario, route.vehicle_id, deliveries, closures)


def build_plan(
    scenario: Scenario,
    seed: int | None = None,
    closures: Sequence = (),
) -> Plan:
    seed = scenario.seed if seed is None else seed
    routes: dict[str, Route] = {
        vehicle.id: _candidate(scenario, vehicle.id, [], closures)
        or Route(vehicle_id=vehicle.id, stops=[_empty_stop(scenario)])
        for vehicle in sorted(scenario.vehicles, key=lambda item: item.id)
    }
    pending: list[Delivery] = []
    unplaced: list[Unplaced] = []
    for delivery in sorted(scenario.deliveries, key=lambda item: (-item.priority, item.id)):
        feasible, reasons = prescreen_delivery(scenario, delivery)
        if feasible:
            pending.append(delivery)
        else:
            unplaced.append(Unplaced(delivery_id=delivery.id, reasons=reasons))

    while pending:
        ranked: list[tuple[int, int, str, list[tuple[int, str, int, Route]]]] = []
        for delivery in pending:
            choices: list[tuple[int, str, int, Route]] = []
            for vehicle_id, route in routes.items():
                for position in range(len(route.stops)):
                    candidate = _route_with_insert(scenario, route, delivery, position, closures)
                    if candidate is not None:
                        choices.append(
                            (
                                candidate.total_travel + candidate.total_wait,
                                vehicle_id,
                                position,
                                candidate,
                            )
                        )
            choices.sort(key=lambda item: (item[0], item[1], item[2]))
            if choices:
                regret = choices[1][0] - choices[0][0] if len(choices) > 1 else 10**9
                ranked.append((-regret, choices[0][0], delivery.id, choices))
        if not ranked:
            for delivery in pending:
                unplaced.append(
                    Unplaced(
                        delivery_id=delivery.id,
                        reasons=diagnose_unplaced(scenario, delivery),
                    )
                )
            break
        _, _, delivery_id, choices = min(ranked, key=lambda item: item[:3])
        _, vehicle_id, _, selected = choices[0]
        routes[vehicle_id] = selected
        pending = [delivery for delivery in pending if delivery.id != delivery_id]

    return Plan(
        version_id=f"{scenario.name}-initial",
        scenario_ref=scenario.name,
        routes=list(routes.values()),
        unplaced=sorted(unplaced, key=lambda item: item.delivery_id),
        seed=seed,
    )


def insert_deliveries(scenario: Scenario, plan: Plan, deliveries: Sequence[Delivery]) -> Plan:
    current = plan
    for delivery in sorted(deliveries, key=lambda item: (-item.priority, item.id)):
        options: list[tuple[int, str, int, Route]] = []
        for route in current.routes:
            for position in range(len(route.stops)):
                candidate = _route_with_insert(scenario, route, delivery, position)
                if candidate is not None:
                    options.append(
                        (
                            candidate.total_travel + candidate.total_wait,
                            route.vehicle_id,
                            position,
                            candidate,
                        )
                    )
        if options:
            _, vehicle_id, _, selected = min(options, key=lambda item: item[:3])
            routes = [
                selected if route.vehicle_id == vehicle_id else route for route in current.routes
            ]
            current = current.model_copy(update={"routes": routes})
        else:
            current = current.model_copy(
                update={
                    "unplaced": [
                        *current.unplaced,
                        Unplaced(
                            delivery_id=delivery.id, reasons=diagnose_unplaced(scenario, delivery)
                        ),
                    ]
                }
            )
    return current
