"""Initial-plan acceptance scoreboard."""

import pytest

from contract.models import Delivery, Plan
from contract.signatures import build_plan

pytestmark = [
    pytest.mark.acceptance,
    pytest.mark.xfail(reason="not implemented: Phase 5 solver", strict=False),
]


def test_build_plan_returns_plan(scenario_micro):
    """R1/R6: the explainable solver produces ordered vehicle routes (I1)."""
    assert isinstance(build_plan(scenario_micro), Plan)


def test_every_delivery_is_placed_or_unplaced_once(scenario_micro):
    """R1/R8: every input delivery is accounted for exactly once (I1)."""
    plan = build_plan(scenario_micro)
    placed = [stop.delivery_id for route in plan.routes for stop in route.stops if stop.delivery_id]
    reported = [item.delivery_id for item in plan.unplaced]
    assert sorted(placed + reported) == sorted(item.id for item in scenario_micro.deliveries)
    assert len(placed + reported) == len(set(placed + reported))


def test_every_unplaced_delivery_has_a_reason(scenario_micro):
    """R8: each delivery the solver cannot place carries a diagnosis (I1)."""
    impossible = Delivery(
        id="OVERSIZE",
        location_id="A",
        demand=max(v.capacity for v in scenario_micro.vehicles) + 1,
        window_open=500,
        window_close=700,
        service_time=5,
    )
    scenario = scenario_micro.model_copy(
        update={"deliveries": [*scenario_micro.deliveries, impossible]}
    )
    item = next(item for item in build_plan(scenario).unplaced if item.delivery_id == "OVERSIZE")
    assert item.reasons


def test_initial_plan_has_one_route_per_vehicle(scenario_micro):
    """R1: the plan exposes a route for each available vehicle (I1)."""
    plan = build_plan(scenario_micro)
    assert {route.vehicle_id for route in plan.routes} == {
        vehicle.id for vehicle in scenario_micro.vehicles
    }


def test_initial_plan_is_deterministic(scenario_micro):
    """R6: equal scenario and seed produce equal plans (I11)."""
    assert build_plan(scenario_micro) == build_plan(scenario_micro)
