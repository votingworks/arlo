import json
from flask.testing import FlaskClient

from ...models import *
from ..helpers import *


def get_discrepancies(client: FlaskClient, election_id: str):
    rv = client.get(f"/api/election/{election_id}/discrepancy")
    return json.loads(rv.data)


def test_jurisdiction_notes(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
    round_1_id: str,
):
    jurisdiction_id = jurisdiction_ids[0]
    notes_url = (
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/discrepancy-notes"
    )

    def notes():
        return (
            JurisdictionNote.query.filter_by(jurisdiction_id=jurisdiction_id)
            .order_by(JurisdictionNote.created_at)
            .all()
        )

    # A jurisdiction is in the response once it's under review, from its
    # first finalize
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    assert get_discrepancies(client, election_id) == {}
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/contest"
    )
    contest = json.loads(rv.data)["contests"][0]
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_1_id}/batches"
    )
    batches = json.loads(rv.data)["batches"]
    batch_tallies = Jurisdiction.query.get(jurisdiction_id).batch_tallies
    for batch in batches:
        rv = put_batch_results(
            client,
            election_id,
            jurisdiction_id,
            round_1_id,
            batch["id"],
            [
                {
                    choice["id"]: batch_tallies[batch["name"]][contest["id"]][
                        choice["id"]
                    ]
                    for choice in contest["choices"]
                }
            ],
        )
        assert_ok(rv)
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_1_id}/batches/finalize",
    )
    assert_ok(rv)

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = post_json(client, notes_url, {"text": "Emailed the JA"})
    assert_ok(rv)
    rv = post_json(client, notes_url, {"text": "One vote off in Batch 1"})
    assert_ok(rv)
    assert [note.text for note in notes()] == [
        "Finalized tallies",
        "Emailed the JA",
        "One vote off in Batch 1",
    ]

    # The response carries the notes, oldest first
    listed = get_discrepancies(client, election_id)[jurisdiction_id]
    assert listed["notes"] == [
        {"createdAt": note.created_at.isoformat(), "text": note.text}
        for note in notes()
    ]
    assert batch_contest_statuses(listed) == {"MATCHES"}

    # A note needs text
    rv = post_json(client, notes_url, {"text": ""})
    assert rv.status_code == 400

    # Jurisdiction admins don't keep notes
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = post_json(client, notes_url, {"text": "Hm"})
    assert rv.status_code == 403


def test_finalizing_and_unfinalizing_tallies_leave_notes(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
    round_1_id: str,
):
    jurisdiction_id = jurisdiction_ids[0]
    finalize_url = f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_1_id}/batches/finalize"

    def jurisdiction_discrepancies():
        return get_discrepancies(client, election_id)[jurisdiction_id]

    # Audit every batch as empty, so each one has a discrepancy, and finalize
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/contest"
    )
    choice_ids = [
        choice["id"] for choice in json.loads(rv.data)["contests"][0]["choices"]
    ]
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_1_id}/batches"
    )
    batches = json.loads(rv.data)["batches"]
    for batch in batches:
        rv = put_batch_results(
            client,
            election_id,
            jurisdiction_id,
            round_1_id,
            batch["id"],
            [{choice_id: 0 for choice_id in choice_ids}],
        )
        assert_ok(rv)
    rv = post_json(client, finalize_url)
    assert_ok(rv)

    # Finalizing leaves a note, so the jurisdiction is in the response from
    # then on
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    finalized = jurisdiction_discrepancies()
    assert [note["text"] for note in finalized["notes"]] == ["Finalized tallies"]
    assert set(finalized["batches"].keys()) == {batch["id"] for batch in batches}

    # So does unfinalizing, which keeps it there while it re-tallies, with its
    # in-progress discrepancies
    rv = client.delete(finalize_url)
    assert_ok(rv)
    unfinalized = jurisdiction_discrepancies()
    assert [note["text"] for note in unfinalized["notes"]] == [
        "Finalized tallies",
        "Unfinalized tallies",
    ]
    assert unfinalized["batches"].keys() == finalized["batches"].keys()
