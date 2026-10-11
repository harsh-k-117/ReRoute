"""tests/unit/api/test_api_endpoints.py - unit: API endpoints in mock mode

Lane : P3 Integration & language lead (single writer for this path)
Stack: pytest · Hypothesis (property-based fuzzing of I1-I12) · ruff
Spec : api
"""
from __future__ import annotations

import pytest


@pytest.mark.xfail(reason="not implemented yet (api)", strict=False)
def test_health() -> None:
    raise NotImplementedError

@pytest.mark.xfail(reason="not implemented yet (api)", strict=False)
def test_scenarios_listed() -> None:
    raise NotImplementedError
