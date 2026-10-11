"""tests/acceptance/test_text_interpretation.py - text -> interpret -> preview -> confirm

Lane : P2 Replan & quality lead (single writer for this path)
Stack: pytest · Hypothesis (property-based fuzzing of I1-I12) · ruff
Spec : R8-R9
"""
from __future__ import annotations

import pytest


@pytest.mark.xfail(reason="not implemented yet (R8-R9)", strict=False)
def test_unknown_location_rejects_whole_report() -> None:
    raise NotImplementedError

@pytest.mark.xfail(reason="not implemented yet (R8-R9)", strict=False)
def test_missing_optional_fields_get_defaults() -> None:
    raise NotImplementedError

@pytest.mark.xfail(reason="not implemented yet (R8-R9)", strict=False)
def test_ambiguous_name_rejected() -> None:
    raise NotImplementedError
