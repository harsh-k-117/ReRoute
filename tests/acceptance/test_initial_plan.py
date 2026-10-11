"""tests/acceptance/test_initial_plan.py - initial plan: arrivals, waits, load line, unplaced reasons

Lane : P2 Replan & quality lead (single writer for this path)
Stack: pytest · Hypothesis (property-based fuzzing of I1-I12) · ruff
Spec : R1-R4
"""
from __future__ import annotations

import pytest


@pytest.mark.xfail(reason="not implemented yet (R1-R4)", strict=False)
def test_arrivals_and_waits_shown() -> None:
    raise NotImplementedError

@pytest.mark.xfail(reason="not implemented yet (R1-R4)", strict=False)
def test_never_overloaded_at_any_point() -> None:
    raise NotImplementedError

@pytest.mark.xfail(reason="not implemented yet (R1-R4)", strict=False)
def test_unplaceable_has_reason() -> None:
    raise NotImplementedError
