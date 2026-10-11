"""Server-side proposal confirmation gate acceptance cases."""

import pytest

pytestmark = [
    pytest.mark.acceptance,
]


def test_interpreted_text_stays_pending_until_confirmation(client_factory):
    """R12/R13: interpretation previews a pending proposal without applying it (I10)."""
    client = client_factory()
    response = client.post(
        "/disruptions/interpret", json={"text": "Van 2 broke down at Cedar at 10:30"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "pending"


def test_confirming_missing_proposal_returns_409(client_factory):
    """R13: the server rejects applying a proposal that was never confirmed (I10)."""
    response = client_factory().post("/proposals/not-a-real-proposal/confirm")
    assert response.status_code == 409


def test_unknown_location_returns_422_and_leaves_state_unchanged(client_factory):
    """R14: unknown places reject the whole report without changing state (I9)."""
    client = client_factory()
    before = client.get("/state").json()
    response = client.post(
        "/disruptions/interpret", json={"text": "Close the road at Atlantis until 11am"}
    )
    after = client.get("/state").json()
    assert response.status_code == 422
    assert after == before


def test_discarded_or_unconfirmed_proposal_does_not_change_state(client_factory):
    """R13: proposing a disruption alone cannot change the current plan (I10)."""
    client = client_factory()
    before = client.get("/state").json()
    proposal = client.post(
        "/disruptions/interpret", json={"text": "Van 2 broke down at Cedar at 10:30"}
    )
    assert proposal.status_code == 200
    assert client.get("/state").json() == before
