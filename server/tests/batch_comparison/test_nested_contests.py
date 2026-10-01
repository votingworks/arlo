import json
import uuid
from flask.testing import FlaskClient

from ...api.contests import JSONDict
from ...models import *  # pylint: disable=wildcard-import
from ..helpers import *  # pylint: disable=wildcard-import


def contest_json(
    name: str,
    jurisdiction_ids: list[str],
    is_targeted: bool = True,
    nested_under_contest_id: str | None = None,
) -> JSONDict:
    return {
        "id": str(uuid.uuid4()),
        "name": name,
        "isTargeted": is_targeted,
        "choices": [
            {"id": str(uuid.uuid4()), "name": "candidate 1", "numVotes": 5000},
            {"id": str(uuid.uuid4()), "name": "candidate 2", "numVotes": 2500},
        ],
        "numWinners": 1,
        "votesAllowed": 1,
        "jurisdictionIds": jurisdiction_ids,
        "nestedUnderContestId": nested_under_contest_id,
    }


def put_contests(client: FlaskClient, election_id: str, contests: list[JSONDict]):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    return put_json(client, f"/api/election/{election_id}/contest", contests)


def test_nested_contests_round_trip(
    client: FlaskClient, election_id: str, jurisdiction_ids: list[str]
):
    parent = contest_json("Parent", jurisdiction_ids)
    child = contest_json(
        "Child", jurisdiction_ids[:1], nested_under_contest_id=parent["id"]
    )
    # The child is sent first to check that save order doesn't matter
    rv = put_contests(client, election_id, [child, parent])
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/contest")
    contests = {contest["name"]: contest for contest in json.loads(rv.data)["contests"]}
    assert contests["Parent"]["nestedUnderContestId"] is None
    assert contests["Child"]["nestedUnderContestId"] == parent["id"]

    # Un-nesting on a later save clears the field
    child["nestedUnderContestId"] = None
    rv = put_contests(client, election_id, [parent, child])
    assert_ok(rv)
    rv = client.get(f"/api/election/{election_id}/contest")
    contests = {contest["name"]: contest for contest in json.loads(rv.data)["contests"]}
    assert contests["Child"]["nestedUnderContestId"] is None


def test_nested_contests_validation(
    client: FlaskClient, election_id: str, jurisdiction_ids: list[str]
):
    def assert_rejected(contests: list[JSONDict], message: str):
        rv = put_contests(client, election_id, contests)
        assert rv.status_code == 400
        assert json.loads(rv.data) == {
            "errors": [{"message": message, "errorType": "Bad Request"}]
        }

    parent = contest_json("Parent", jurisdiction_ids)
    child = contest_json(
        "Child", jurisdiction_ids, nested_under_contest_id=parent["id"]
    )

    assert_rejected(
        [child],
        "Contest Child is nested under a contest that doesn't exist",
    )

    opportunistic_parent = contest_json("Parent", jurisdiction_ids, is_targeted=False)
    assert_rejected(
        [
            opportunistic_parent,
            contest_json(
                "Child",
                jurisdiction_ids,
                nested_under_contest_id=opportunistic_parent["id"],
            ),
        ],
        "Contest Child and the contest it is nested under must both be targeted",
    )
    assert_rejected(
        [
            parent,
            contest_json(
                "Child",
                jurisdiction_ids,
                is_targeted=False,
                nested_under_contest_id=parent["id"],
            ),
        ],
        "Contest Child and the contest it is nested under must both be targeted",
    )

    self_nested = contest_json("Loop", jurisdiction_ids)
    self_nested["nestedUnderContestId"] = self_nested["id"]
    assert_rejected([self_nested], "Nested contests must not form a cycle")

    parent["nestedUnderContestId"] = child["id"]
    assert_rejected([parent, child], "Nested contests must not form a cycle")


def test_nested_contests_rejected_for_non_batch_comparison(
    client: FlaskClient, org_id: str
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    ballot_polling_election_id = create_election(
        client,
        audit_name="Test Audit nested contests ballot polling",
        audit_type=AuditType.BALLOT_POLLING,
        audit_math_type=AuditMathType.BRAVO,
        organization_id=org_id,
    )
    rv = upload_jurisdictions_file(
        client,
        io.BytesIO(
            f"Jurisdiction,Admin Email\nJ1,j1-{ballot_polling_election_id}@example.com\n".encode()
        ),
        ballot_polling_election_id,
    )
    assert_ok(rv)
    jurisdiction_id = str(
        Jurisdiction.query.filter_by(election_id=ballot_polling_election_id).one().id
    )
    parent = contest_json("Parent", [jurisdiction_id])
    child = contest_json(
        "Child", [jurisdiction_id], nested_under_contest_id=parent["id"]
    )
    for contest in [parent, child]:
        contest["totalBallotsCast"] = 10000
    rv = put_contests(client, ballot_polling_election_id, [parent, child])
    assert rv.status_code == 400
    assert json.loads(rv.data) == {
        "errors": [
            {
                "message": "nestedUnderContestId is only supported for batch comparison audits",
                "errorType": "Bad Request",
            }
        ]
    }
