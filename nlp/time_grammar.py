"""nlp/time_grammar.py - "10:30", "3pm", "until 14:00", "for 2 hours", "in 30 min" -> minutes since midnight

Lane : P3 Integration & language lead (single writer for this path)
Stack: Python 3.12 · rule-based parser + exact-match location resolver (primary, offline) · optional LLM extractor (Anthropic API, JSON output) behind a flag, with timeout + fallback (star)
Spec : D1
"""
from __future__ import annotations
