from fastapi import APIRouter, Depends

from api.deps import get_store
from api.store import SessionStore
from contract.models import Plan
from verify.validator import validate

router = APIRouter()


@router.post("/validate")
def validate_plan(
    plan: Plan | None = None,
    store: SessionStore = Depends(get_store),  # noqa: B008
) -> object:
    return validate(store.scenario, plan or store.plan)
