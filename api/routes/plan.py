import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.deps import get_store
from api.mock import fixture
from api.settings import mock_mode
from api.store import SessionStore, load_scenario
from contract.models import Plan, Scenario, ValidationReport
from engine.construct import build_plan
from verify.validator import validate

router = APIRouter()


class InitialPlanResponse(BaseModel):
    plan: Plan
    validation_report: ValidationReport


class InitialPlanRequest(BaseModel):
    scenario: str | None = None
    inline_scenario: dict[str, Any] | None = None


@router.post("/plan/initial", response_model=InitialPlanResponse)
def initial_plan(
    request: InitialPlanRequest,
    store: SessionStore = Depends(get_store),  # noqa: B008
) -> InitialPlanResponse:
    if mock_mode() and request.inline_scenario is None:
        plan = Plan.model_validate_json(json.dumps(fixture("plan_initial.json")))
        report = ValidationReport.model_validate_json(
            json.dumps(fixture("validation_report_ok.json"))
        )
        return InitialPlanResponse(plan=plan, validation_report=report)
    try:
        scenario = (
            Scenario.model_validate(request.inline_scenario)
            if request.inline_scenario is not None
            else load_scenario(request.scenario or store.scenario.name)
        )
        plan = build_plan(scenario)
        report = validate(scenario, plan)
        if not report.passed:
            raise HTTPException(status_code=500, detail=report.model_dump(mode="json"))
        store.scenario = scenario
        store.plan = plan
        store.versions[plan.version_id] = plan
        return InitialPlanResponse(plan=plan, validation_report=report)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown scenario: {exc.args[0]}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
