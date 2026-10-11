"""Reason-carrying plan comparison acceptance cases."""

import pytest

from contract.models import Delivery, RoadClosure, UrgentDelivery
from contract.signatures import classify, replan

pytestmark = pytest.mark.acceptance


def test_diff_classifies_every_delivery(scenario_micro, plan_micro):
    """R15: every delivery receives a kept, moved, or broken row (I1)."""
    result = classify(plan_micro, plan_micro)
    assert {row.delivery_id for row in result.rows} == {
        delivery.id for delivery in scenario_micro.deliveries
    }
    assert all(row.classification in {"kept", "moved", "broken"} for row in result.rows)


def test_no_op_replan_keeps_every_delivery(scenario_micro, plan_micro):
    """R15: a no-op replan reports all deliveries as kept (I12)."""
    unused_edge = RoadClosure(
        type="road_closure",
        a="C",
        b="F",
        mode="add_minutes",
        value=20,
        both_directions=True,
        start=900,
        end=1000,
    )
    result = replan(scenario_micro, plan_micro, unused_edge)
    assert result.diff.rows
    assert all(row.classification == "kept" for row in result.diff.rows)


def test_every_moved_or_broken_row_has_a_cause(scenario_micro, plan_micro):
    """R15: every changed customer assignment has a reason (I8)."""
    event = RoadClosure(
        type="road_closure",
        a="A",
        b="B",
        mode="add_minutes",
        value=25,
        both_directions=True,
        start=480,
        end=700,
    )
    result = replan(scenario_micro, plan_micro, event)
    changed = [row for row in result.diff.rows if row.classification != "kept"]
    assert all(row.cause_code and row.sentence for row in changed)


def test_diff_counts_match_classifications(scenario_micro, plan_micro):
    """R15: summary counts agree with row classifications (I1/I8)."""
    result = classify(plan_micro, plan_micro)
    assert result.kept_count == sum(row.classification == "kept" for row in result.rows)
    assert result.moved_count == sum(row.classification == "moved" for row in result.rows)
    assert result.broken_count == sum(row.classification == "broken" for row in result.rows)


def test_kept_rows_name_the_original_vehicle_and_eta(scenario_micro, plan_micro):
    """R15: kept rows retain before/after customer assignment details (I8)."""
    result = classify(plan_micro, plan_micro)
    for row in result.rows:
        if row.classification == "kept":
            assert row.before_vehicle_id == row.after_vehicle_id
            assert row.before_eta is not None and row.after_eta is not None


def test_new_delivery_diff_row_has_new_badge(scenario_micro, plan_micro):
    """R11/R15: a newly placed delivery is visible as NEW in the comparison (I8)."""
    delivery = Delivery(
        id="NEW-1",
        location_id="C",
        demand=1,
        window_open=650,
        window_close=700,
        service_time=5,
        priority=2,
        release_time=630,
    )
    event = UrgentDelivery(type="urgent_delivery", delivery=delivery, report_time=630)
    result = replan(scenario_micro, plan_micro, event)
    row = next(row for row in result.diff.rows if row.delivery_id == "NEW-1")
    assert row.badge == "NEW"


def test_broken_row_can_show_earliest_feasible_eta(scenario_micro, plan_micro):
    """R8/R15: broken delivery explanation may include a negotiation ETA hint (I8)."""
    result = classify(plan_micro, plan_micro)
    assert all(
        row.earliest_feasible_eta is None or row.earliest_feasible_eta >= 0
        for row in result.rows
        if row.classification == "broken"
    )
