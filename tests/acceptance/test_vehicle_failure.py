"""Vehicle-failure replanning acceptance cases."""

import pytest

from contract.models import VehicleFailure
from contract.signatures import replan, snapshot

pytestmark = pytest.mark.acceptance


def test_failure_replans_at_stated_time(scenario_micro, plan_micro):
    """R10/R11: failure time is used as the replanning boundary (I5/I6)."""
    event = VehicleFailure(type="vehicle_failure", vehicle_id="V2", at_time=515)
    result = replan(scenario_micro, plan_micro, event)
    assert result.validation_report.passed
    assert result.plan.version_id != plan_micro.version_id


def test_failed_vehicle_has_no_stop_after_failure(scenario_micro, plan_micro):
    """R10/R15: failed vehicle receives no future stops after failure time (I5)."""
    event = VehicleFailure(type="vehicle_failure", vehicle_id="V2", at_time=515)
    result = replan(scenario_micro, plan_micro, event)
    route = next(route for route in result.plan.routes if route.vehicle_id == "V2")
    assert all(stop.service_start <= 515 for stop in route.stops)


def test_completed_stops_remain_byte_identical(scenario_micro, plan_micro):
    """R11/R15: completed stops stay fixed during a failure replan (I6)."""
    event = VehicleFailure(type="vehicle_failure", vehicle_id="V2", at_time=515)
    result = replan(scenario_micro, plan_micro, event)
    before = next(route for route in plan_micro.routes if route.vehicle_id == "V2")
    after = next(route for route in result.plan.routes if route.vehicle_id == "V2")
    assert before.stops[0] == after.stops[0]


def test_snapshot_marks_finished_work_frozen(scenario_micro, plan_micro):
    """R11: snapshot records the frozen prefix at the current time (I6)."""
    state = snapshot(scenario_micro, plan_micro, 515)
    v1 = next(vehicle for vehicle in state.vehicles if vehicle.vehicle_id == "V1")
    assert v1.frozen_stops
    assert all(stop.frozen for stop in v1.frozen_stops)
