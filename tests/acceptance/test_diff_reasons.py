"""tests/acceptance/test_diff_reasons.py - side-by-side diff: every moved/broken row has a cause

Lane : P2 Replan & quality lead (single writer for this path)
Stack: pytest · Hypothesis (property-based fuzzing of I1-I12) · ruff
Spec : R11-R12
"""
from __future__ import annotations

import pytest


@pytest.mark.xfail(reason="not implemented yet (R11-R12)", strict=False)
def test_every_non_kept_row_has_cause() -> None:
    raise NotImplementedError

@pytest.mark.xfail(reason="not implemented yet (R11-R12)", strict=False)
def test_noop_replan_all_kept() -> None:
    raise NotImplementedError
