"""engine/trace.py - decision trace, e.g. 'cheapest feasible slot +6 min; runner-up V3 +11' (star)

Lane : P1 Algorithm lead (single writer for this path)
Stack: Python 3.12 · Pydantic v2 · pure + deterministic (seeded RNG, iteration budgets, ties by ID: D10) · tests: pytest · lint: ruff · custom solver: regret-2 insertion + ruin-and-recreate (no solver dependency; OR-Tools only in benchmarks)
Spec : explainability
"""
from __future__ import annotations
