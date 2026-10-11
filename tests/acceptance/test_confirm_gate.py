"""tests/acceptance/test_confirm_gate.py - server-enforced confirm gate

Lane : P2 Replan & quality lead (single writer for this path)
Stack: pytest · Hypothesis (property-based fuzzing of I1-I12) · ruff
Spec : R10
"""
from __future__ import annotations

import pytest


@pytest.mark.xfail(reason="not implemented yet (R10)", strict=False)
def test_apply_without_confirm_is_409() -> None:
    raise NotImplementedError

@pytest.mark.xfail(reason="not implemented yet (R10)", strict=False)
def test_unknown_place_is_422() -> None:
    raise NotImplementedError

@pytest.mark.xfail(reason="not implemented yet (R10)", strict=False)
def test_state_unchanged_after_rejection() -> None:
    raise NotImplementedError
