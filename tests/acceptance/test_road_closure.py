"""tests/acceptance/test_road_closure.py - closure disruption end to end

Lane : P2 Replan & quality lead (single writer for this path)
Stack: pytest · Hypothesis (property-based fuzzing of I1-I12) · ruff
Spec : R5
"""
from __future__ import annotations

import pytest


@pytest.mark.xfail(reason="not implemented yet (R5)", strict=False)
def test_closure_raises_edge_time_for_departures_in_window() -> None:
    raise NotImplementedError

@pytest.mark.xfail(reason="not implemented yet (R5)", strict=False)
def test_closure_replan_validates() -> None:
    raise NotImplementedError
