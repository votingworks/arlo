import json
from flask.testing import FlaskClient

from ...models import *
from ..helpers import *


def test_batch_discrepancy_review(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
    contest_id: str,
    round_1_id: str,
):
    jurisdiction_id = jurisdiction_ids[0]
    batches_url = f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_1_id}/batches"

    # Batch 1 is one vote short of its reported tallies; the rest match
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(batches_url)
    batches = json.loads(rv.data)["batches"]
    batch_1 = next(batch for batch in batches if batch["name"] == "Batch 1")
    choice_ids = [choice.id for choice in Contest.query.get(contest_id).choices]
    batch_tallies = Jurisdiction.query.get(jurisdiction_id).batch_tallies
    for batch in batches:
        results = {
            choice_id: batch_tallies[batch["name"]][contest_id][choice_id]
            for choice_id in choice_ids
        }
        if batch is batch_1:
            results[choice_ids[0]] -= 1
        rv = put_json(
            client,
            f"{batches_url}/{batch['id']}/results",
            [{"name": "Tally Sheet #1", "results": results}],
        )
        assert_ok(rv)

    def review_url(batch, path):
        return f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/batches/{batch['id']}/{path}"

    def status(batch):
        return Batch.query.get(batch["id"]).discrepancy_status

    def notes(batch):
        return [
            (note.user_email, note.text)
            for note in Batch.query.get(batch["id"]).discrepancy_notes
        ]

    # Until the jurisdiction finalizes, there's nothing to review
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = put_json(
        client, review_url(batch_1, "discrepancy-status"), {"status": "ACCEPTED"}
    )
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Conflict",
                "message": "Batch does not have a discrepancy under review",
            }
        ]
    }
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = post_json(client, f"{batches_url}/finalize")
    assert_ok(rv)
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)

    # The discrepancy listing carries each batch's status, notes, and margin impact
    rv = client.get(f"/api/election/{election_id}/discrepancy")
    review = json.loads(rv.data)[jurisdiction_id]
    assert set(review) == {batch["id"] for batch in batches}
    for batch in batches:
        if batch is not batch_1:
            assert review[batch["id"]]["status"] == "ACCEPTED"
            assert review[batch["id"]]["discrepancies"] == {}
    batch_1_review = review[batch_1["id"]]
    assert batch_1_review["name"] == "Batch 1"
    assert batch_1_review["isExtra"] is False
    assert batch_1_review["status"] == "NEEDS_REVIEW"
    assert batch_1_review["notes"] == []
    contest_review = batch_1_review["discrepancies"][contest_id]
    assert contest_review["discrepancies"] == {
        choice_ids[0]: 1,
        choice_ids[1]: 0,
        choice_ids[2]: 0,
    }
    assert contest_review["changeInMargin"] == 1
    assert contest_review["numBallots"] == 500

    # Support can mark the discrepancy accepted or the jurisdiction contacted
    rv = put_json(
        client, review_url(batch_1, "discrepancy-status"), {"status": "ACCEPTED"}
    )
    assert_ok(rv)
    assert status(batch_1) == BatchDiscrepancyStatus.ACCEPTED
    rv = put_json(
        client,
        review_url(batch_1, "discrepancy-status"),
        {"status": "JURISDICTION_CONTACTED"},
    )
    assert_ok(rv)
    assert status(batch_1) == BatchDiscrepancyStatus.JURISDICTION_CONTACTED

    # Only the two statuses support decides on can be requested
    rv = put_json(
        client, review_url(batch_1, "discrepancy-status"), {"status": "RE_TALLYING"}
    )
    assert rv.status_code == 400

    # Notes are attributed to the audit admin, or to the support user logged in
    # as them
    rv = post_json(
        client, review_url(batch_1, "discrepancy-notes"), {"text": "Emailed the JA"}
    )
    assert_ok(rv)
    set_support_user(client, DEFAULT_SUPPORT_EMAIL)
    rv = post_json(
        client, review_url(batch_1, "discrepancy-notes"), {"text": "One vote off"}
    )
    assert_ok(rv)
    clear_support_user(client)
    admin_note = (DEFAULT_AA_EMAIL, "Emailed the JA")
    support_note = (DEFAULT_SUPPORT_EMAIL, "One vote off")
    assert notes(batch_1) == [admin_note, support_note]

    # The listing carries the notes, with ids for deleting them
    rv = client.get(f"/api/election/{election_id}/discrepancy")
    listed_notes = json.loads(rv.data)[jurisdiction_id][batch_1["id"]]["notes"]
    assert [(note["userEmail"], note["text"]) for note in listed_notes] == [
        admin_note,
        support_note,
    ]
    assert [note["id"] for note in listed_notes] == [
        note.id for note in Batch.query.get(batch_1["id"]).discrepancy_notes
    ]

    # A note needs text
    rv = post_json(client, review_url(batch_1, "discrepancy-notes"), {"text": ""})
    assert rv.status_code == 400

    # Notes can be deleted
    note_ids = [note.id for note in Batch.query.get(batch_1["id"]).discrepancy_notes]
    rv = client.delete(review_url(batch_1, f"discrepancy-notes/{note_ids[0]}"))
    assert_ok(rv)
    assert notes(batch_1) == [support_note]
    rv = client.delete(review_url(batch_1, "discrepancy-notes/not-a-note-id"))
    assert rv.status_code == 404

    # A batch is only reachable through its own jurisdiction
    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/batches/{batch_1['id']}/discrepancy-status",
        {"status": "ACCEPTED"},
    )
    assert rv.status_code == 404

    # Once the jurisdiction is reopened, the batch is being re-tallied, not reviewed
    rv = client.delete(f"{batches_url}/finalize")
    assert_ok(rv)
    assert status(batch_1) == BatchDiscrepancyStatus.RE_TALLYING
    rv = client.get(f"/api/election/{election_id}/discrepancy")
    assert (
        json.loads(rv.data)[jurisdiction_id][batch_1["id"]]["status"] == "RE_TALLYING"
    )
    rv = put_json(
        client, review_url(batch_1, "discrepancy-status"), {"status": "ACCEPTED"}
    )
    assert rv.status_code == 409

    # Jurisdiction admins don't review discrepancies
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = put_json(
        client, review_url(batch_1, "discrepancy-status"), {"status": "ACCEPTED"}
    )
    assert rv.status_code == 403
    rv = post_json(client, review_url(batch_1, "discrepancy-notes"), {"text": "Hm"})
    assert rv.status_code == 403
