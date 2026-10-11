"""nlp/llm_extractor.py - OPTIONAL (star): Anthropic API extractor behind a flag; mention must appear verbatim and resolve exactly

Lane : P3 Integration & language lead (single writer for this path)
Stack: Python 3.12 · rule-based parser + exact-match location resolver (primary, offline) · optional LLM extractor (Anthropic API, JSON output) behind a flag, with timeout + fallback (star)
Spec : D8
"""
from __future__ import annotations

# Never sees the location list. Timeout + fallback to rules. Flag: REROUTE_LLM_EXTRACTOR=1
