from fastapi import APIRouter, Depends

from api.deps import get_store
from api.store import SessionStore
from replan.snapshot import snapshot

router = APIRouter()


@router.get("/state")
def state(store: SessionStore = Depends(get_store)) -> dict[str, object]:  # noqa: B008
    return {
        "plan_version": store.plan.version_id,
        "plan": store.plan,
        "snapshot": snapshot(store.scenario, store.plan, store.scenario.now),
    }
