"""nlp/interpreter.py - interpret(text) -> Proposal with spans, assumptions, warnings, rejections

Lane : P3 Integration & language lead (single writer for this path)
Stack: Python 3.12 · rule-based parser + exact-match location resolver (primary, offline) · optional LLM extractor (Anthropic API, JSON output) behind a flag, with timeout + fallback (star)
Spec : D8, I9, I10
"""
from __future__ import annotations

from contract.models import Proposal, Scenario


def interpret(text: str, scenario: Scenario, now: int) -> Proposal:
    """Two events in one report, unknown place, partial-name collision, missing time, contradictions -> rejected or flagged."""
    raise NotImplementedError
