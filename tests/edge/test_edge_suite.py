"""tests/edge/test_edge_suite.py - edge suite: failure at t=0 / exactly at stop end / idle vehicle; overlapping closures; replan-of-replan

Lane : P2 Replan & quality lead (single writer for this path)
Stack: pytest · Hypothesis (property-based fuzzing of I1-I12) · ruff
Spec : edge
"""
from __future__ import annotations

import pytest


@pytest.mark.xfail(reason="not implemented yet (edge)", strict=False)
def test_failure_at_t0() -> None:
    raise NotImplementedError

@pytest.mark.xfail(reason="not implemented yet (edge)", strict=False)
def test_failure_at_stop_end() -> None:
    raise NotImplementedError

@pytest.mark.xfail(reason="not implemented yet (edge)", strict=False)
def test_failure_on_idle_vehicle() -> None:
    raise NotImplementedError

@pytest.mark.xfail(reason="not implemented yet (edge)", strict=False)
def test_closure_on_unused_edge() -> None:
    raise NotImplementedError

@pytest.mark.xfail(reason="not implemented yet (edge)", strict=False)
def test_replan_of_replan() -> None:
    raise NotImplementedError
