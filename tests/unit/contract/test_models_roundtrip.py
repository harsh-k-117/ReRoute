"""Round-trip checks for the shared contract fixtures."""

import json
from pathlib import Path

import pytest
from pydantic import TypeAdapter, ValidationError

from contract.models import (
    Diff,
    Delivery,
    Disruption,
    Plan,
    Proposal,
    ReplanResult,
    Scenario,
    ValidationReport,
)

FIXTURES = Path(__file__).parents[3] / "contract" / "fixtures"


@pytest.mark.parametrize(
    ("filename", "model"),
    [
        ("scenario_micro.json", Scenario),
        ("scenario_city.json", Scenario),
        ("plan_micro.json", Plan),
        ("plan_initial.json", Plan),
        ("proposal_failure.json", Proposal),
        ("proposal.json", Proposal),
        ("replan_result_closure.json", ReplanResult),
        ("replan_result.json", ReplanResult),
        ("validation_report_ok.json", ValidationReport),
        ("validation_report.json", ValidationReport),
        ("diff.json", Diff),
    ],
)
def test_fixture_canonical_json_roundtrip(filename: str, model: type) -> None:
    fixture = (FIXTURES / filename).read_text()
    instance = model.model_validate_json(fixture)
    serialized = instance.model_dump_json()
    assert json.loads(model.model_validate_json(serialized).model_dump_json()) == json.loads(
        serialized
    )


@pytest.mark.parametrize(
    "filename",
    ["disruption_closure.json", "disruption_failure.json", "disruption_urgent.json"],
)
def test_disruption_fixture_canonical_json_roundtrip(filename: str) -> None:
    adapter = TypeAdapter(Disruption)
    instance = adapter.validate_json((FIXTURES / filename).read_text())
    serialized = adapter.dump_json(instance)
    assert json.loads(adapter.dump_json(adapter.validate_json(serialized))) == json.loads(
        serialized
    )


def test_invalid_delivery_and_disruption_are_rejected() -> None:
    with pytest.raises(ValidationError):
        Delivery(
            id="bad",
            location_id="A",
            demand=-1,
            window_open=10,
            window_close=20,
            service_time=1,
        )
    with pytest.raises(ValidationError):
        Delivery(
            id="bad-window",
            location_id="A",
            demand=1,
            window_open=20,
            window_close=10,
            service_time=1,
        )
    with pytest.raises(ValidationError):
        TypeAdapter(Disruption).validate_python({"type": "unknown"})
