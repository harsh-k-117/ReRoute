"""tests/unit/nlp/test_nlp_resolver.py - unit: exact-match resolver

Lane : P3 Integration & language lead (single writer for this path)
Stack: pytest · Hypothesis (property-based fuzzing of I1-I12) · ruff
Spec : D8
"""
from __future__ import annotations

import pytest


@pytest.mark.xfail(reason="not implemented yet (D8)", strict=False)
def test_case_space_punctuation_normalized() -> None:
    raise NotImplementedError

@pytest.mark.xfail(reason="not implemented yet (D8)", strict=False)
def test_alias_resolves() -> None:
    raise NotImplementedError

@pytest.mark.xfail(reason="not implemented yet (D8)", strict=False)
def test_ambiguous_rejected() -> None:
    raise NotImplementedError
