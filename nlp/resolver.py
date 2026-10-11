"""nlp/resolver.py - exact-match location/vehicle resolver: normalize case/space/punctuation, aliases, ambiguous -> reject

Lane : P3 Integration & language lead (single writer for this path)
Stack: Python 3.12 · rule-based parser + exact-match location resolver (primary, offline) · optional LLM extractor (Anthropic API, JSON output) behind a flag, with timeout + fallback (star)
Spec : D8, I9
"""
from __future__ import annotations

from contract.models import Scenario


class Unresolved(ValueError): ...


class Ambiguous(ValueError): ...


def resolve_location(mention: str, scenario: Scenario) -> str:
    """Exact match only after normalization. No fuzzy matching, ever."""
    raise NotImplementedError
