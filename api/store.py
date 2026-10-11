"""Thread-safe in-memory session and plan-version store."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from threading import RLock

from contract.models import Plan, Proposal, ReplanResult, Scenario
from data.importers import import_scenario_json
from engine.construct import build_plan
from verify.validator import validate


@dataclass
class SessionStore:
    scenario: Scenario
    plan: Plan
    versions: dict[str, Plan] = field(default_factory=dict)
    proposals: dict[str, Proposal] = field(default_factory=dict)
    lock: RLock = field(default_factory=RLock, repr=False)

    @classmethod
    def from_scenario(cls, scenario: Scenario) -> SessionStore:
        plan = build_plan(scenario)
        if not validate(scenario, plan).passed:
            raise ValueError("initial plan failed validation")
        return cls(scenario=scenario, plan=plan, versions={plan.version_id: plan})

    def save_proposal(self, proposal: Proposal) -> Proposal:
        with self.lock:
            self.proposals[proposal.id] = proposal
        return proposal

    def get_proposal(self, proposal_id: str) -> Proposal | None:
        with self.lock:
            return self.proposals.get(proposal_id)

    def commit(self, result: ReplanResult) -> ReplanResult:
        with self.lock:
            self.plan = result.plan
            self.versions[result.plan.version_id] = result.plan
        return result

    def restore(self, version_id: str) -> Plan:
        with self.lock:
            restored = self.versions.get(version_id)
            if restored is None:
                raise KeyError(version_id)
            self.plan = restored
            return restored


def load_scenario(name: str, scenario_dir: Path | None = None) -> Scenario:
    """Load a named scenario from the configured scenario directory."""
    root = scenario_dir or Path(__file__).parents[1] / "data" / "scenarios"
    path = root / f"{name}.json"
    if not path.is_file():
        raise KeyError(name)
    return import_scenario_json(path)


def available_scenarios(scenario_dir: Path | None = None) -> list[Scenario]:
    root = scenario_dir or Path(__file__).parents[1] / "data" / "scenarios"
    return [import_scenario_json(path) for path in sorted(root.glob("*.json"))]


def default_store() -> SessionStore:
    try:
        return SessionStore.from_scenario(load_scenario("micro"))
    except KeyError:
        return SessionStore.from_scenario(load_scenario("baseline"))
