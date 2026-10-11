import json
from pathlib import Path

from pydantic import TypeAdapter

from contract.models import Disruption, Scenario
from data.generators import generate_city, generate_stress
from engine.construct import build_plan
from scripts.gen_scenarios import generate_scenario_pack


def test_city_generator_is_deterministic_and_has_metric_symmetric_matrix():
    first = generate_city(seed=21, n_deliveries=12, n_vehicles=3)
    second = generate_city(seed=21, n_deliveries=12, n_vehicles=3)

    assert first.model_dump(mode="json") == second.model_dump(mode="json")
    for i, row in enumerate(first.travel_times):
        assert row[i] == 0
        for j, minutes in enumerate(row):
            assert minutes == first.travel_times[j][i]
            for k in range(len(row)):
                assert minutes <= first.travel_times[i][k] + first.travel_times[k][j]


def test_city_impossible_orders_are_reported_by_the_engine():
    scenario = generate_city(seed=7, n_deliveries=2, n_vehicles=3)
    plan = build_plan(scenario)

    assert len(plan.unplaced) == 2
    assert all(row.reasons for row in plan.unplaced)


def test_stress_generator_is_deterministic_and_supports_target_scale():
    first = generate_stress(seed=13, n_deliveries=100, n_vehicles=10)
    second = generate_stress(seed=13, n_deliveries=100, n_vehicles=10)
    target = generate_stress(seed=13, n_deliveries=200, n_vehicles=15)

    assert first.model_dump(mode="json") == second.model_dump(mode="json")
    assert len(target.deliveries) == 200
    assert len(target.vehicles) == 15


def test_generated_pack_scenarios_validate_and_baseline_builds():
    pack = generate_scenario_pack()
    assert set(pack) == {
        "baseline",
        "closure",
        "failure",
        "urgent",
        "cascade",
        "stress",
        "impossible",
    }
    for bundle in pack.values():
        scenario = Scenario.model_validate(bundle["scenario"])
        assert scenario.deliveries
        assert isinstance(json.dumps(bundle), str)
        for disruption in bundle["disruptions"]:
            TypeAdapter(Disruption).validate_python(disruption)

    for path in Path("data/scenarios").glob("*.json"):
        bundle = json.loads(path.read_text(encoding="utf-8"))
        Scenario.model_validate(bundle["scenario"])
        for disruption in bundle["disruptions"]:
            TypeAdapter(Disruption).validate_python(disruption)

    baseline = Scenario.model_validate(pack["baseline"]["scenario"])
    baseline_plan = build_plan(baseline)
    assert baseline_plan.routes
    assert not baseline_plan.unplaced
    impossible = Scenario.model_validate(pack["impossible"]["scenario"])
    result = build_plan(impossible)
    assert len(result.unplaced) >= 1
    assert all(item.reasons for item in result.unplaced)
