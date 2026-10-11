"""Small JSON-file CLI for plan, replan, and validation workflows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pydantic import TypeAdapter

from contract.models import Disruption, Plan
from contract.signatures import replan, validate
from data.importers import import_scenario_json
from engine.construct import build_plan


def _read(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write(value: object) -> None:
    print(json.dumps(value.model_dump(mode="json"), indent=2))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="reroute")
    commands = parser.add_subparsers(dest="command", required=True)

    plan_parser = commands.add_parser("plan")
    plan_parser.add_argument("scenario")

    replan_parser = commands.add_parser("replan")
    replan_parser.add_argument("scenario")
    replan_parser.add_argument("plan")
    replan_parser.add_argument("disruption")

    validate_parser = commands.add_parser("validate")
    validate_parser.add_argument("scenario")
    validate_parser.add_argument("plan")

    args = parser.parse_args(argv)
    scenario = import_scenario_json(args.scenario)
    if args.command == "plan":
        _write(build_plan(scenario))
        return 0
    plan = Plan.model_validate(_read(args.plan))
    if args.command == "validate":
        report = validate(scenario, plan)
        _write(report)
        return 0 if report.passed else 1
    disruption = TypeAdapter(Disruption).validate_python(_read(args.disruption))
    result = replan(scenario, plan, disruption)
    _write(result)
    return 0
