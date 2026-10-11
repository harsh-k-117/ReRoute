"""Import-stable function contracts for independently developed ReRoute lanes."""

from __future__ import annotations

from collections.abc import Sequence

from contract.models import (
    Delivery,
    Diff,
    Disruption,
    Plan,
    PlanSnapshot,
    Proposal,
    Reason,
    ReplanResult,
    Route,
    Scenario,
    Stop,
    ValidationReport,
)


def simulate_route(scenario: Scenario, vehicle_id: str, stops: Sequence[Stop]) -> Route:
    """Simulate one vehicle route, including travel, waiting, service, and load."""
    from engine.simulate import simulate_route as implementation

    return implementation(scenario, vehicle_id, stops)


def build_plan(scenario: Scenario) -> Plan:
    """Build a deterministic initial delivery plan for a scenario."""
    from engine.construct import build_plan as implementation

    return implementation(scenario)


def insert_deliveries(scenario: Scenario, plan: Plan, deliveries: Sequence[Delivery]) -> Plan:
    """Insert deliveries into a plan while preserving route feasibility."""
    from engine.construct import insert_deliveries as implementation

    return implementation(scenario, plan, deliveries)


def improve(scenario: Scenario, plan: Plan, iterations: int = 0) -> Plan:
    """Improve a feasible plan using a deterministic bounded search."""
    from engine.improve import improve as implementation

    return implementation(scenario, plan, iterations)


def diagnose_unplaced(scenario: Scenario, delivery: Delivery) -> list[Reason]:
    """Return reason-coded feasibility diagnostics for a delivery."""
    from engine.diagnose import diagnose_unplaced as implementation

    return implementation(scenario, delivery)


def snapshot(scenario: Scenario, plan: Plan, now: int) -> PlanSnapshot:
    """Freeze completed and committed work and compute each vehicle's ready state."""
    from replan.snapshot import snapshot as implementation

    return implementation(scenario, plan, now)


def replan(scenario: Scenario, plan: Plan, disruption: Disruption) -> ReplanResult:
    """Apply a confirmed disruption and produce a validated revised plan."""
    from replan.replan import replan as implementation

    return implementation(scenario, plan, disruption)


def validate(
    scenario: Scenario,
    plan: Plan,
    previous_plan: Plan | None = None,
    disruption: object | None = None,
    diff: object | None = None,
    proposal: object | None = None,
) -> ValidationReport:
    """Independently validate a plan against all routing invariants."""
    from verify.validator import validate as implementation

    return implementation(
        scenario=scenario,
        plan=plan,
        previous_plan=previous_plan,
        disruption=disruption,
        diff=diff,
        proposal=proposal,
    )


def classify(previous: Plan, revised: Plan) -> Diff:
    """Classify every delivery as kept, moved, or broken with a reason."""
    from diff.classify import classify as implementation

    return implementation(previous, revised)


def interpret(text: str, scenario: Scenario) -> Proposal:
    """Interpret dispatcher text as a pending proposal; never apply it."""
    from nlp.interpreter import interpret as implementation

    return implementation(text, scenario)
