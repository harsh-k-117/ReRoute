"""tests/acceptance/test_vehicle_failure.py - failure disruption: orphaned parcels, rescue pickup, nothing after failure

Lane : P2 Replan & quality lead (single writer for this path)
Stack: pytest · Hypothesis (property-based fuzzing of I1-I12) · ruff
Spec : R6
"""
from __future__ import annotations

import pytest


@pytest.mark.xfail(reason="not implemented yet (R6)", strict=False)
def test_nothing_after_failure_time() -> None:
    raise NotImplementedError

@pytest.mark.xfail(reason="not implemented yet (R6)", strict=False)
def test_rescue_pickup_added() -> None:
    raise NotImplementedError

@pytest.mark.xfail(reason="not implemented yet (R6)", strict=False)
def test_completed_stops_unchanged() -> None:
    raise NotImplementedError
