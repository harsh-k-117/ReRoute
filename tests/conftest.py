"""tests/conftest.py - shared fixtures (micro scenario, seeds)

Lane : P2 Replan & quality lead (single writer for this path)
Stack: pytest · Hypothesis (property-based fuzzing of I1-I12) · ruff
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).resolve().parent.parent / "contract" / "fixtures"


@pytest.fixture
def micro_scenario_json() -> dict:
    return json.loads((FIXTURES / "scenario_micro.json").read_text())
