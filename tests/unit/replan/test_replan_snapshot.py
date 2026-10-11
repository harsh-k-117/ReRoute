"""tests/unit/replan/test_replan_snapshot.py - unit: snapshot / freeze rule

Lane : P2 Replan & quality lead (single writer for this path)
Stack: pytest · Hypothesis (property-based fuzzing of I1-I12) · ruff
Spec : D5
"""
from __future__ import annotations

import pytest


@pytest.mark.xfail(reason="not implemented yet (D5)", strict=False)
def test_freeze_in_progress_and_driving() -> None:
    raise NotImplementedError
