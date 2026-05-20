import json
import uuid
from flask.testing import FlaskClient

from ...models import *
from ..helpers import *


def _runoff_contest(jurisdiction_ids: list[str], **overrides) -> dict:
    contest = {
        "id": str(uuid.uuid4()),
        "name": "Runoff Contest",
        "isTargeted": True,
        "choices": [
            {"id": str(uuid.uuid4()), "name": "Alice", "numVotes": 4000},
            {"id": str(uuid.uuid4()), "name": "Bob", "numVotes": 3500},
            {"id": str(uuid.uuid4()), "name": "Carla", "numVotes": 1500},
            {"id": str(uuid.uuid4()), "name": "Dan", "numVotes": 1000},
        ],
        "numWinners": 1,
        "votesAllowed": 1,
        "jurisdictionIds": jurisdiction_ids,
        "isSubjectToRunoff": True,
    }
    contest.update(overrides)
    return contest


def test_runoff_flag_serialized_for_batch_comparison(
    client: FlaskClient, election_id: str, jurisdiction_ids: list[str]
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    contest = _runoff_contest(jurisdiction_ids)

    rv = put_json(client, f"/api/election/{election_id}/contest", [contest])
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/contest")
    contests = json.loads(rv.data)["contests"]
    assert len(contests) == 1
    assert contests[0]["isSubjectToRunoff"] is True


def test_runoff_flag_defaults_to_false_when_omitted(
    client: FlaskClient, election_id: str, jurisdiction_ids: list[str]
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    contest = _runoff_contest(jurisdiction_ids)
    del contest["isSubjectToRunoff"]

    rv = put_json(client, f"/api/election/{election_id}/contest", [contest])
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/contest")
    contests = json.loads(rv.data)["contests"]
    assert contests[0]["isSubjectToRunoff"] is False


def test_runoff_flag_rejects_num_winners_not_one(
    client: FlaskClient, election_id: str, jurisdiction_ids: list[str]
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    contest = _runoff_contest(jurisdiction_ids, numWinners=2)

    rv = put_json(client, f"/api/election/{election_id}/contest", [contest])
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": "isSubjectToRunoff can only be true for contests with num_winners=1",
                "errorType": "Bad Request",
            }
        ]
    }


def test_runoff_flag_requires_three_or_more_choices(
    client: FlaskClient, election_id: str, jurisdiction_ids: list[str]
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    contest = _runoff_contest(
        jurisdiction_ids,
        choices=[
            {"id": str(uuid.uuid4()), "name": "Alice", "numVotes": 4000},
            {"id": str(uuid.uuid4()), "name": "Bob", "numVotes": 3500},
        ],
    )

    rv = put_json(client, f"/api/election/{election_id}/contest", [contest])
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": "isSubjectToRunoff can only be true for contests with at least 3 choices",
                "errorType": "Bad Request",
            }
        ]
    }
