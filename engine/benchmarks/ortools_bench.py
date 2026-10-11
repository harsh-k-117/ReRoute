"""engine/benchmarks/ortools_bench.py - OR-Tools comparison, benchmarks ONLY (star; optional extra `bench`)

Lane : P1 Algorithm lead (single writer for this path)
Stack: Python 3.12 · Pydantic v2 · pure + deterministic (seeded RNG, iteration budgets, ties by ID: D10) · tests: pytest · lint: ruff · custom solver: regret-2 insertion + ruin-and-recreate (no solver dependency; OR-Tools only in benchmarks)
Spec : star
"""
from __future__ import annotations

# import ortools lazily inside functions: it is an optional dependency
