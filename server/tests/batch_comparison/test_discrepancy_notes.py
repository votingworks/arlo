import json
from datetime import timedelta
from flask.testing import FlaskClient

from ...database import db_session
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

    # A jurisdiction without discrepancies isn't in the response until it has
    # a note
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    assert get_discrepancies(client, election_id) == {}

    rv = post_json(client, notes_url, {"text": "Emailed the JA"})
    assert_ok(rv)
    rv = post_json(client, notes_url, {"text": "One vote off in Batch 1"})
    assert_ok(rv)
    assert [note.text for note in notes()] == [
        "Emailed the JA",
        "One vote off in Batch 1",
    ]

    # The notes keep the jurisdiction in the response, oldest first
    assert get_discrepancies(client, election_id) == {
        jurisdiction_id: {
            "notes": [
                {"createdAt": note.created_at.isoformat(), "text": note.text}
                for note in notes()
            ],
            "batches": {},
        }
    }

    # Only a note written since the round started keeps it there
    round = Round.query.get(round_1_id)
    for note in notes():
        note.created_at = round.created_at - timedelta(minutes=1)
    db_session.commit()
    assert get_discrepancies(client, election_id) == {}

    # A note needs text
    rv = post_json(client, notes_url, {"text": ""})
    assert rv.status_code == 400

    # Jurisdiction admins don't keep notes
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = post_json(client, notes_url, {"text": "Hm"})
    assert rv.status_code == 403
