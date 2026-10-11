"""Regenerate the seven checked-in demo scenario bundles."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from contract.models import RoadClosure, UrgentDelivery, VehicleFailure
from data.generators import BRIDGE_EDGE, generate_city, generate_stress
from engine.construct import build_plan

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "data" / "scenarios"
SEED = 7


def _bundle(
    scenario: Any, description: str, disruptions: list[Any] | None = None
) -> dict[str, Any]:
    return {
        "name": scenario.name,
        "description": description,
        "scenario": scenario.model_dump(mode="json"),
        "disruptions": [item.model_dump(mode="json") for item in disruptions or []],
    }


def _plan_failure(scenario: Any) -> VehicleFailure:
    plan = build_plan(scenario, seed=SEED)
    route = max(
        plan.routes,
        key=lambda item: (
            sum(stop.delivery_id is not None for stop in item.stops),
            item.vehicle_id,
        ),
    )
    delivery_stops = [stop for stop in route.stops if stop.delivery_id is not None]
    fail_after = (
        delivery_stops[max(0, (len(delivery_stops) - 1) // 2)].depart + 1
        if delivery_stops
        else scenario.start_time + 30
    )
    return VehicleFailure(
        type="vehicle_failure",
        vehicle_id=route.vehicle_id,
        at_time=fail_after,
        transfer_minutes=scenario.config.transfer_minutes,
    )


def generate_scenario_pack() -> dict[str, dict[str, Any]]:
    baseline = generate_city(SEED, n_deliveries=12, n_vehicles=4, include_impossible=False)
    baseline = baseline.model_copy(update={"name": "baseline"})
    closure_scenario = baseline.model_copy(update={"name": "closure"})
    failure_scenario = baseline.model_copy(update={"name": "failure"})
    urgent_scenario = baseline.model_copy(update={"name": "urgent"})
    cascade_scenario = baseline.model_copy(update={"name": "cascade"})

    closure = RoadClosure(
        type="road_closure",
        a=BRIDGE_EDGE[0],
        b=BRIDGE_EDGE[1],
        mode="add_minutes",
        value=20,
        both_directions=True,
        start=540,
        end=660,
    )
    failure = _plan_failure(baseline)
    urgent = UrgentDelivery(
        type="urgent_delivery",
        delivery={
            "id": "NEW001",
            "location_id": "DECCAN",
            "demand": 3,
            "window_open": 570,
            "window_close": 630,
            "service_time": 10,
            "priority": 2,
            "release_time": 540,
        },
        report_time=540,
        priority=2,
    )
    impossible = generate_city(SEED, n_deliveries=2, n_vehicles=3, include_impossible=True)
    impossible = impossible.model_copy(update={"name": "impossible"})
    stress = generate_stress(SEED, n_deliveries=100, n_vehicles=10)

    return {
        "baseline": _bundle(baseline, "Initial morning plan with feasible deliveries."),
        "closure": _bundle(
            closure_scenario,
            "Road closure adds time on the shared Sangamwadi–Bund Garden edge.",
            [closure],
        ),
        "failure": _bundle(
            failure_scenario,
            "Failure of the busiest vehicle during its route; completed stops stay fixed.",
            [failure],
        ),
        "urgent": _bundle(
            urgent_scenario,
            "Priority urgent delivery released during the shift.",
            [urgent],
        ),
        "cascade": _bundle(
            cascade_scenario,
            "Road closure followed by a vehicle failure during the same shift.",
            [closure, failure],
        ),
        "stress": _bundle(
            stress, "Deterministic engine workload at 100 deliveries and 10 vehicles."
        ),
        "impossible": _bundle(
            impossible,
            "Contains one oversize delivery and one delivery unreachable before its window closes.",
        ),
    }


def write_scenario_pack(output_dir: Path = DEFAULT_OUTPUT) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name, bundle in generate_scenario_pack().items():
        target = output_dir / f"{name}.json"
        target.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        written.append(target)
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out", type=Path, default=DEFAULT_OUTPUT, help="directory for generated JSON files"
    )
    args = parser.parse_args()
    for path in write_scenario_pack(args.out):
        print(path)


if __name__ == "__main__":
    main()
