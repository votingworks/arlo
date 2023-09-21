from flask.testing import FlaskClient

from ..helpers import *  # pylint: disable=wildcard-import


def test_support_get_jurisdiction_batch_comparison(
    client: FlaskClient,
    org_id: str,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id: str,  # pylint: disable=unused-argument
):
    set_support_user(client, DEFAULT_SUPPORT_EMAIL)
    rv = client.get(f"/api/support/jurisdictions/{jurisdiction_ids[0]}")
    compare_json(
        json.loads(rv.data),
        {
            "id": jurisdiction_ids[0],
            "name": "J1",
            "organization": {
                "id": org_id,
                "name": "Test Org test_support_get_jurisdiction_batch_comparison",
            },
            "election": {
                "id": election_id,
                "auditName": "Test Audit test_support_get_jurisdiction_batch_comparison",
                "auditType": "BATCH_COMPARISON",
                "online": False,
                "deletedAt": None,
            },
            "jurisdictionAdmins": [{"email": default_ja_email(election_id)}],
            "auditBoards": [],
            "recordedResultsAt": None,
        },
    )
