"""Road-closure replanning acceptance cases."""

import pytest

from contract.models import RoadClosure
from contract.signatures import replan

pytestmark = pytest.mark.acceptance


def test_closure_replans_from_previous_plan(scenario_micro, plan_micro):
    """R9/R15: a timed edge closure produces a revised plan (I4/I12)."""
    event = RoadClosure(
        type="road_closure",
        a="A",
        b="B",
        mode="add_minutes",
        value=15,
        both_directions=True,
        start=540,
        end=660,
    )
    result = replan(scenario_micro, plan_micro, event)
    assert result.previous_plan_ref == plan_micro.version_id
    assert result.plan.version_id != plan_micro.version_id


def test_closure_period_and_edge_are_preserved(scenario_micro, plan_micro):
    """R9: closure applies to its named edge and stated departure period (I4)."""
    event = RoadClosure(
        type="road_closure",
        a="A",
        b="B",
        mode="add_minutes",
        value=15,
        both_directions=False,
        start=540,
        end=660,
    )
    result = replan(scenario_micro, plan_micro, event)
    assert result.validation_report.passed


def test_closure_diff_explains_every_changed_delivery(scenario_micro, plan_micro):
    """R9/R15: changed assignments include a customer-readable cause (I8)."""
    event = RoadClosure(
        type="road_closure",
        a="A",
        b="B",
        mode="add_minutes",
        value=30,
        both_directions=True,
        start=480,
        end=700,
    )
    result = replan(scenario_micro, plan_micro, event)
    assert all(row.cause_code and row.sentence for row in result.diff.rows)


def test_closure_never_silently_serves_a_delivery_late(scenario_micro, plan_micro):
    """R4/R9: closure repair preserves hard time windows (I3/I4)."""
    event = RoadClosure(
        type="road_closure",
        a="A",
        b="B",
        mode="add_minutes",
        value=60,
        both_directions=True,
        start=480,
        end=700,
    )
    result = replan(scenario_micro, plan_micro, event)
    assert all(
        stop.window_close is None or stop.service_start <= stop.window_close
        for route in result.plan.routes
        for stop in route.stops
    )
