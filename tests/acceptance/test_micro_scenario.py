"""Hand-computed simulator contract for the small golden scenario."""

import pytest

from contract.signatures import simulate_route

pytestmark = pytest.mark.acceptance


def _route(plan, vehicle_id):
    return next(route for route in plan.routes if route.vehicle_id == vehicle_id)


def test_v1_arrival_wait_service_and_load_match_fixture(scenario_micro, plan_micro):
    """R2/R4/R7: fixed V1 sequence reproduces hand-computed times and loads (I2/I3)."""
    expected = _route(plan_micro, "V1")
    actual = simulate_route(scenario_micro, "V1", expected.stops)
    assert [
        (stop.arrival, stop.wait, stop.service_start, stop.depart, stop.load_after)
        for stop in actual.stops
    ] == [(480, 0, 480, 480, 5), (490, 10, 500, 505, 2), (510, 0, 510, 515, 0)]


def test_v2_capacity_binding_route_never_exceeds_capacity(scenario_micro, plan_micro):
    """R2/R3: the route starting at capacity and after each drop remains feasible (I2)."""
    actual = simulate_route(scenario_micro, "V2", _route(plan_micro, "V2").stops)
    capacity = next(vehicle.capacity for vehicle in scenario_micro.vehicles if vehicle.id == "V2")
    assert actual.stops[0].load_after == capacity
    assert all(0 <= stop.load_after <= capacity for stop in actual.stops)


def test_no_vehicle_load_exceeds_capacity_at_any_stop(scenario_micro, plan_micro):
    """R2/R3: all routes stay within vehicle capacity at every stop (I2)."""
    capacities = {vehicle.id: vehicle.capacity for vehicle in scenario_micro.vehicles}
    for expected in plan_micro.routes:
        actual = simulate_route(scenario_micro, expected.vehicle_id, expected.stops)
        assert all(0 <= stop.load_after <= capacities[expected.vehicle_id] for stop in actual.stops)


def test_v3_wait_is_exposed_and_matches_window(scenario_micro, plan_micro):
    """R4/R7: early arrival wait is explicit and service starts at window opening (I3)."""
    expected = _route(plan_micro, "V3")
    actual = simulate_route(scenario_micro, "V3", expected.stops)
    last = actual.stops[-1]
    assert (last.arrival, last.wait, last.service_start) == (525, 5, 530)


def test_all_micro_routes_match_the_golden_plan(scenario_micro, plan_micro):
    """R1/R2/R4/R7: each fixed route reproduces its fixture arithmetic (I2/I3)."""
    for expected in plan_micro.routes:
        actual = simulate_route(scenario_micro, expected.vehicle_id, expected.stops)
        assert actual == expected


def test_simulation_uses_the_supplied_matrix_only(scenario_micro, plan_micro):
    """R5/R7: route travel follows the scenario matrix, without external mapping (I4)."""
    expected = _route(plan_micro, "V1")
    actual = simulate_route(scenario_micro, "V1", expected.stops)
    assert actual.stops[1].arrival == scenario_micro.start_time + scenario_micro.travel_times[0][1]
