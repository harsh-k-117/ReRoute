"""verify/validator.py - validate(): hard gate before any plan is shown or committed

Lane : P2 Replan & quality lead (single writer for this path)
Stack: Python 3.12 · stdlib + contract models ONLY. MUST NOT import the engine's simulator (independent validator) · pytest · Hypothesis
Spec : I1-I12
"""
from __future__ import annotations

from contract.models import Disruption, Plan, Scenario, ValidationReport


def validate(scenario: Scenario, plan: Plan, disruptions: list[Disruption] | None = None, now: int | None = None) -> ValidationReport:
    raise NotImplementedError
