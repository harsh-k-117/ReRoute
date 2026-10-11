"""tests/unit/nlp/test_nlp_time_grammar.py - unit: time grammar

Lane : P3 Integration & language lead (single writer for this path)
Stack: pytest · Hypothesis (property-based fuzzing of I1-I12) · ruff
Spec : D1
"""
from __future__ import annotations

import pytest


@pytest.mark.xfail(reason="not implemented yet (D1)", strict=False)
def test_parses_10_30() -> None:
    raise NotImplementedError

@pytest.mark.xfail(reason="not implemented yet (D1)", strict=False)
def test_parses_3pm() -> None:
    raise NotImplementedError

@pytest.mark.xfail(reason="not implemented yet (D1)", strict=False)
def test_parses_in_30_min() -> None:
    raise NotImplementedError
