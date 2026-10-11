"""tests/unit/diff/test_diff_classify.py - unit: kept/moved/broken thresholds

Lane : P2 Replan & quality lead (single writer for this path)
Stack: pytest · Hypothesis (property-based fuzzing of I1-I12) · ruff
Spec : D7
"""
from __future__ import annotations

import pytest


@pytest.mark.xfail(reason="not implemented yet (D7)", strict=False)
def test_kept_within_five_minutes() -> None:
    raise NotImplementedError
