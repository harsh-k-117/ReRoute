"""verify/invariants.py - I1-I12 checks written from the spec, not from the engine

Lane : P2 Replan & quality lead (single writer for this path)
Stack: Python 3.12 · stdlib + contract models ONLY. MUST NOT import the engine's simulator (independent validator) · pytest · Hypothesis
Spec : I1-I12
"""
from __future__ import annotations

# One function per invariant: check_i1 ... check_i12
