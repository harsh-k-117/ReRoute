"""tests/unit/verify/test_verify_validator.py - unit: validator catches deliberately broken plans

Lane : P2 Replan & quality lead (single writer for this path)
Stack: pytest · Hypothesis (property-based fuzzing of I1-I12) · ruff
Spec : I2, I3
"""
from __future__ import annotations

import pytest


@pytest.mark.xfail(reason="not implemented yet (I2, I3)", strict=False)
def test_detects_overload() -> None:
    raise NotImplementedError

@pytest.mark.xfail(reason="not implemented yet (I2, I3)", strict=False)
def test_detects_late_start() -> None:
    raise NotImplementedError
