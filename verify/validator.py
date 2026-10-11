from __future__ import annotations

from contract.models import Plan, Proposal, Scenario, ValidationReport

from .invariants import _collect_invariants


def validate(
    scenario: Scenario,
    plan: Plan,
    previous_plan: Plan | None = None,
    disruption: object | None = None,
    diff: object | None = None,
    proposal: Proposal | None = None,
) -> ValidationReport:
    """Run the full validator against a plan and any contextual replan metadata."""
    checks = _collect_invariants(
        scenario=scenario,
        plan=plan,
        previous_plan=previous_plan,
        disruption=disruption,
        diff=diff,
        proposal=proposal,
        comparison_plan=None,
    )
    return ValidationReport(checks=checks, passed=all(item.passed for item in checks))


__all__ = ["validate"]
