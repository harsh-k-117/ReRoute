"""nlp/rules.py - rule-based extraction for road_closure / vehicle_failure / urgent_delivery

Lane : P3 Integration & language lead (single writer for this path)
Stack: Python 3.12 · rule-based parser + exact-match location resolver (primary, offline) · optional LLM extractor (Anthropic API, JSON output) behind a flag, with timeout + fallback (star)
Spec : D8
"""
from __future__ import annotations
