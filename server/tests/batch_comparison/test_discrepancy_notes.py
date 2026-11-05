from flask.testing import FlaskClient

from ...models import *
from ..helpers import *


def test_jurisdiction_notes(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
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

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = post_json(client, notes_url, {"text": "Emailed the JA"})
    assert_ok(rv)
    rv = post_json(client, notes_url, {"text": "One vote off in Batch 1"})
    assert_ok(rv)
    assert [note.text for note in notes()] == [
        "Emailed the JA",
        "One vote off in Batch 1",
    ]

    # A note needs text
    rv = post_json(client, notes_url, {"text": ""})
    assert rv.status_code == 400

    # Jurisdiction admins don't keep notes
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = post_json(client, notes_url, {"text": "Hm"})
    assert rv.status_code == 403
