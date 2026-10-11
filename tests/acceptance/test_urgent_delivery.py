"""tests/acceptance/test_urgent_delivery.py - urgent delivery: depot pickup, release time, NEW badge

Lane : P2 Replan & quality lead (single writer for this path)
Stack: pytest · Hypothesis (property-based fuzzing of I1-I12) · ruff
Spec : R7
"""
from __future__ import annotations

import pytest


@pytest.mark.xfail(reason="not implemented yet (R7)", strict=False)
def test_urgent_placed_or_broken_with_reason() -> None:
    raise NotImplementedError

@pytest.mark.xfail(reason="not implemented yet (R7)", strict=False)
def test_load_never_exceeds_capacity() -> None:
    raise NotImplementedError
