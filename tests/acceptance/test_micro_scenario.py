"""tests/acceptance/test_micro_scenario.py - hand-checkable micro-scenario (3 vehicles, 8 deliveries)

Lane : P2 Replan & quality lead (single writer for this path)
Stack: pytest · Hypothesis (property-based fuzzing of I1-I12) · ruff
Spec : R1
"""
from __future__ import annotations

import pytest


@pytest.mark.xfail(reason="not implemented yet (R1)", strict=False)
def test_expected_arrivals_match_hand_calculation() -> None:
    raise NotImplementedError
