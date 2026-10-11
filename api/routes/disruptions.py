from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.deps import get_store
from api.store import SessionStore
from contract.models import Disruption, Proposal
from contract.signatures import replan
from nlp.interpreter import interpret

router = APIRouter()


class TextRequest(BaseModel):
    text: str


def _preview(proposal: Proposal, store: SessionStore) -> Proposal:
    if proposal.rejections:
        return proposal
    result = replan(store.scenario, store.plan, proposal.disruption)
    return proposal.model_copy(update={"impact_preview": result})


@router.post("/disruptions/preview")
def preview(
    disruption: Disruption,
    store: SessionStore = Depends(get_store),  # noqa: B008
) -> Proposal:
    proposal = Proposal(
        id=f"proposal-{len(store.proposals) + 1}",
        source="form",
        disruption=disruption,
    )
    proposal = _preview(proposal, store)
    store.save_proposal(proposal)
    return proposal


@router.post("/disruptions/interpret")
def interpret_report(
    request: TextRequest,
    store: SessionStore = Depends(get_store),  # noqa: B008
) -> Proposal:
    try:
        proposal = interpret(request.text, store.scenario)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    proposal = _preview(proposal, store)
    store.save_proposal(proposal)
    if proposal.rejections:
        raise HTTPException(status_code=422, detail=proposal.model_dump(mode="json"))
    return proposal
