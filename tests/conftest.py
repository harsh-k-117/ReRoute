"""Shared fixtures for acceptance and validator tests."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

from contract.models import Plan, Scenario

ROOT = Path(__file__).parents[1]
CONTRACT_FIXTURES = ROOT / "contract" / "fixtures"


def load_fixture(name: str) -> Any:
    """Load a JSON fixture by filename from contract/fixtures."""
    return (CONTRACT_FIXTURES / name).read_text()


@pytest.fixture
def scenario_micro() -> Scenario:
    return Scenario.model_validate_json(load_fixture("scenario_micro.json"))


@pytest.fixture
def plan_micro() -> Plan:
    return Plan.model_validate_json(load_fixture("plan_micro.json"))


@pytest.fixture
def client_factory() -> Callable[[], Any]:
    """Return a factory so API tests can construct a fresh FastAPI client per case."""

    def create_client() -> Any:
        from fastapi.testclient import TestClient

        from api.main import app

        return TestClient(app)

    return create_client


def mutate(plan: Plan, case: str) -> Plan:
    """Return a deliberately malformed plan for independent-validator tests."""
    routes = list(plan.routes)
    route = routes[0]
    stops = list(route.stops)
    if case == "overloaded":
        stops[0] = stops[0].model_copy(update={"load_after": 10_000})
    elif case == "window_violation":
        index = next(i for i, stop in enumerate(stops) if stop.delivery_id is not None)
        stops[index] = stops[index].model_copy(
            update={"service_start": stops[index].window_close + 1}
        )
    elif case == "stop_after_failure":
        route = route.model_copy(update={"failed_at": stops[0].depart})
    elif case == "duplicate_delivery":
        stops.append(next(stop for stop in stops if stop.delivery_id is not None))
    elif case == "missing_delivery":
        index = max(i for i, stop in enumerate(stops) if stop.delivery_id is not None)
        del stops[index]
    elif case == "pickup_after_delivery":
        index = next(i for i, stop in enumerate(stops) if stop.delivery_id is not None)
        pickup = stops[index].model_copy(update={"kind": "pickup"})
        stops.insert(index + 1, pickup)
    else:
        raise ValueError(f"unknown mutation case: {case}")
    if case != "stop_after_failure":
        route = route.model_copy(update={"stops": stops})
    routes[0] = route
    return plan.model_copy(update={"routes": routes})
