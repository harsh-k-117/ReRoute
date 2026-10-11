"""Urgent-delivery replanning acceptance cases."""

import pytest

from contract.models import Delivery, UrgentDelivery
from contract.signatures import replan

pytestmark = [
    pytest.mark.acceptance,
    pytest.mark.xfail(reason="not implemented: Phase 8 replanner", strict=False),
]


def _urgent(location_id="C", demand=1, close=700):
    delivery = Delivery(
        id="NEW-1", location_id=location_id, demand=demand, window_open=650,
        window_close=close, service_time=5, priority=2, release_time=630,
    )
    return UrgentDelivery(type="urgent_delivery", delivery=delivery, report_time=630)


def test_urgent_delivery_is_added_to_revised_plan(scenario_micro, plan_micro):
    """R11: a feasible urgent delivery is placed during the day (I1)."""
    result = replan(scenario_micro, plan_micro, _urgent())
    ids = [stop.delivery_id for route in result.plan.routes for stop in route.stops]
    assert "NEW-1" in ids


def test_urgent_delivery_is_badged_new(scenario_micro, plan_micro):
    """R11/R15: placed urgent delivery is visibly marked NEW in the result (I8)."""
    result = replan(scenario_micro, plan_micro, _urgent())
    stop = next(
        stop for route in result.plan.routes for stop in route.stops
        if stop.delivery_id == "NEW-1"
    )
    assert "NEW" in stop.badges


def test_urgent_pickup_occurs_at_depot_after_report_time(scenario_micro, plan_micro):
    """R11: urgent parcel pickup is at depot and respects its report-time release (I7)."""
    result = replan(scenario_micro, plan_micro, _urgent())
    pickups = [
        stop for route in result.plan.routes for stop in route.stops
        if stop.kind == "pickup" and "NEW-1" in stop.parcel_ids
    ]
    assert pickups
    assert all(stop.location_id == scenario_micro.depot_id for stop in pickups)
    assert all(stop.service_start >= 630 for stop in pickups)


def test_urgent_replan_never_overloads_any_route(scenario_micro, plan_micro):
    """R2/R11: urgent insertion respects capacity at every recorded step (I2)."""
    result = replan(scenario_micro, plan_micro, _urgent())
    capacities = {vehicle.id: vehicle.capacity for vehicle in scenario_micro.vehicles}
    for route in result.plan.routes:
        assert all(0 <= stop.load_after <= capacities[route.vehicle_id] for stop in route.stops)


def test_unplaceable_urgent_delivery_has_a_reason(scenario_micro, plan_micro):
    """R8/R11: an urgent delivery that cannot fit is reported with a reason (I1)."""
    result = replan(scenario_micro, plan_micro, _urgent(location_id="F", demand=99))
    item = next(item for item in result.plan.unplaced if item.delivery_id == "NEW-1")
    assert item.reasons
