"""Free-text interpretation acceptance cases."""

import pytest

from contract.models import Proposal
from contract.signatures import interpret

pytestmark = pytest.mark.acceptance


def test_text_report_becomes_pending_proposal(scenario_micro):
    """R12/R13: interpreting a report returns a proposal that still needs confirmation (I10)."""
    proposal = interpret("Close the road between Alder and Birch from 9am to 11am", scenario_micro)
    assert isinstance(proposal, Proposal)
    assert proposal.status == "pending"


def test_text_interpretation_does_not_apply_a_plan(scenario_micro):
    """R13: text interpretation creates a proposal without mutating the input (I10)."""
    before = scenario_micro.model_dump()
    interpret("Van 2 broke down at Cedar at 10:30", scenario_micro)
    assert scenario_micro.model_dump() == before


def test_unknown_location_is_rejected_not_guessed(scenario_micro):
    """R14: an unrecognized place is rejected rather than fuzzy-matched (I9)."""
    proposal = interpret("Close the road at Atlantis until 11am", scenario_micro)
    assert proposal.rejections


def test_text_fields_link_to_valid_source_spans(scenario_micro):
    """R12: extracted field highlights point inside the original report (I10)."""
    text = "Van 2 broke down at Cedar at 10:30"
    proposal = interpret(text, scenario_micro)
    assert proposal.original_text == text
    assert all(0 <= span.start <= span.end <= len(text) for span in proposal.spans)


def test_ambiguous_vehicle_reference_is_rejected(scenario_micro):
    """R14: ambiguous vehicle names reject the whole report instead of guessing (I9)."""
    proposal = interpret("Van failed at 10:30", scenario_micro)
    assert proposal.rejections
