"""tests/unit/nlp/test_nlp_hostile_phrasings.py - 30+ phrasings incl. hostile ones

Lane : P3 Integration & language lead (single writer for this path)
Stack: pytest · Hypothesis (property-based fuzzing of I1-I12) · ruff
Spec : D8
"""
from __future__ import annotations

import pytest


@pytest.mark.xfail(reason="not implemented yet (D8)", strict=False)
def test_unknown_place() -> None:
    raise NotImplementedError

@pytest.mark.xfail(reason="not implemented yet (D8)", strict=False)
def test_partial_name_two_matches() -> None:
    raise NotImplementedError

@pytest.mark.xfail(reason="not implemented yet (D8)", strict=False)
def test_two_events_in_one_report() -> None:
    raise NotImplementedError
