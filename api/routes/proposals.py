from fastapi import APIRouter, Depends, HTTPException

from api.deps import get_store
from api.store import SessionStore
from contract.models import Proposal, ProposalStatus, ReplanResult
from contract.signatures import replan

router = APIRouter()


@router.post("/proposals/{proposal_id}/confirm", response_model=ReplanResult)
def confirm(proposal_id: str, store: SessionStore = Depends(get_store)) -> ReplanResult:  # noqa: B008
    proposal = store.get_proposal(proposal_id)
    if proposal is None or proposal.status != ProposalStatus.PENDING:
        raise HTTPException(status_code=409, detail="Proposal must exist and be pending.")
    if proposal.rejections:
        raise HTTPException(status_code=422, detail=proposal.model_dump(mode="json"))
    confirmed = proposal.model_copy(update={"status": ProposalStatus.CONFIRMED})
    store.save_proposal(confirmed)
    try:
        return store.commit(replan(store.scenario, store.plan, confirmed.disruption))
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/proposals/{proposal_id}/discard", response_model=Proposal)
def discard(proposal_id: str, store: SessionStore = Depends(get_store)) -> Proposal:  # noqa: B008
    proposal = store.get_proposal(proposal_id)
    if proposal is None:
        raise HTTPException(status_code=409, detail="Proposal does not exist.")
    discarded = proposal.model_copy(update={"status": ProposalStatus.DISCARDED})
    store.save_proposal(discarded)
    return discarded


@router.get("/versions")
def versions(store: SessionStore = Depends(get_store)) -> list[dict[str, object]]:  # noqa: B008
    return [
        {"id": version_id, "current": version_id == store.plan.version_id}
        for version_id in store.versions
    ]


@router.post("/versions/{version_id}/restore")
def restore(version_id: str, store: SessionStore = Depends(get_store)) -> object:  # noqa: B008
    try:
        return store.restore(version_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown plan version: {version_id}") from exc
