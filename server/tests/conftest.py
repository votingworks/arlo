import io, uuid, json, os
from typing import List, Generator
from flask.testing import FlaskClient
from flask import jsonify, abort
import pytest

# Before we set up the Flask app, set the env. That way it will use the test
# config and we can still run tests without setting the env var manually.
os.environ["FLASK_ENV"] = "test"
# pylint: disable=wrong-import-position

from ..app import app, db
from ..models import *  # pylint: disable=wildcard-import
from ..auth import (
    UserType,
    with_election_access,
    with_jurisdiction_access,
    with_audit_board_access,
)
from .helpers import *  # pylint: disable=wildcard-import
from ..bgcompute import (
    bgcompute_update_election_jurisdictions_file,
    bgcompute_update_ballot_manifest_file,
)


# The fixtures in this module are available in any test via dependency
# injection.


@pytest.fixture
def client() -> Generator[FlaskClient, None, None]:
    app.config["TESTING"] = True
    client = app.test_client()

    with app.app_context():
        db.drop_all()
        db.create_all()

    yield client

    db.session.commit()


@pytest.fixture
def election_id(client: FlaskClient) -> str:
    return create_election(client)


@pytest.fixture
def jurisdiction_ids(client: FlaskClient, election_id: str) -> List[str]:
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/file",
        data={
            "jurisdictions": (
                # We expect the API to order the jurisdictions by name, so we
                # upload them out of order.
                io.BytesIO(
                    (
                        "Jurisdiction,Admin Email\n"
                        f"J2,{DEFAULT_JA_EMAIL}\n"
                        "J3,j3@example.com\n"
                        f"J1,{DEFAULT_JA_EMAIL}\n"
                    ).encode()
                ),
                "jurisdictions.csv",
            )
        },
    )
    assert_ok(rv)
    bgcompute_update_election_jurisdictions_file()
    jurisdictions = (
        Jurisdiction.query.filter_by(election_id=election_id)
        .order_by(Jurisdiction.name)
        .all()
    )
    return [j.id for j in jurisdictions]


@pytest.fixture
def contest_ids(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
) -> List[str]:
    contests = [
        {
            "id": str(uuid.uuid4()),
            "name": "Contest 1",
            "isTargeted": True,
            "choices": [
                {"id": str(uuid.uuid4()), "name": "candidate 1", "numVotes": 600,},
                {"id": str(uuid.uuid4()), "name": "candidate 2", "numVotes": 400,},
            ],
            "totalBallotsCast": 1000,
            "numWinners": 1,
            "votesAllowed": 1,
            "jurisdictionIds": jurisdiction_ids,
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Contest 2",
            "isTargeted": False,
            "choices": [
                {"id": str(uuid.uuid4()), "name": "candidate 1", "numVotes": 200,},
                {"id": str(uuid.uuid4()), "name": "candidate 2", "numVotes": 300,},
                {"id": str(uuid.uuid4()), "name": "candidate 3", "numVotes": 100,},
            ],
            "totalBallotsCast": 600,
            "numWinners": 2,
            "votesAllowed": 2,
            "jurisdictionIds": jurisdiction_ids[:2],
        },
    ]
    rv = put_json(client, f"/api/election/{election_id}/contest", contests)
    assert_ok(rv)
    return [str(c["id"]) for c in contests]


@pytest.fixture
def election_settings(client: FlaskClient, election_id: str):
    settings = {
        "electionName": "Test Election",
        "online": True,
        "randomSeed": "1234567890",
        "riskLimit": 10,
        "state": USState.California,
    }
    rv = put_json(client, f"/api/election/{election_id}/settings", settings)
    assert_ok(rv)


@pytest.fixture
def manifests(client: FlaskClient, election_id: str, jurisdiction_ids: List[str]):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest",
        data={
            "manifest": (
                io.BytesIO(
                    b"Batch Name,Number of Ballots\n"
                    b"1,23\n"
                    b"2,101\n"
                    b"3,122\n"
                    b"4,400"
                ),
                "manifest.csv",
            )
        },
    )
    assert_ok(rv)
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/ballot-manifest",
        data={
            "manifest": (
                io.BytesIO(
                    b"Batch Name,Number of Ballots\n"
                    b"1,20\n"
                    b"2,10\n"
                    b"3,220\n"
                    b"4,40"
                ),
                "manifest.csv",
            )
        },
    )
    assert_ok(rv)
    bgcompute_update_ballot_manifest_file()


@pytest.fixture
def round_1_id(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    contest_ids: str,  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
) -> str:
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {"roundNum": 1, "sampleSize": SAMPLE_SIZE_ROUND_1},
    )
    assert_ok(rv)
    rv = client.get(f"/api/election/{election_id}/round",)
    rounds = json.loads(rv.data)["rounds"]
    return str(rounds[0]["id"])


@pytest.fixture
def round_2_id(
    client: FlaskClient,
    election_id: str,
    contest_ids: str,
    round_1_id: str,
    audit_board_round_1_ids: List[str],  # pylint: disable=unused-argument
) -> str:
    run_audit_round(round_1_id, contest_ids[0], 0.55)

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = post_json(client, f"/api/election/{election_id}/round", {"roundNum": 2},)
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/round",)
    rounds = json.loads(rv.data)["rounds"]
    return str(rounds[1]["id"])


@pytest.fixture
def audit_board_round_1_ids(
    client: FlaskClient, election_id: str, jurisdiction_ids: str, round_1_id: str,
) -> List[str]:
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
        [{"name": "Audit Board #1"}, {"name": "Audit Board #2"}],
    )
    assert_ok(rv)
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board"
    )
    audit_boards = json.loads(rv.data)["auditBoards"]
    return [ab["id"] for ab in audit_boards]


@pytest.fixture
def audit_board_round_2_ids(
    client: FlaskClient, election_id: str, jurisdiction_ids: str, round_2_id: str,
) -> List[str]:
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_2_id}/audit-board",
        [
            {"name": "Audit Board #1"},
            {"name": "Audit Board #2"},
            {"name": "Audit Board #3"},
        ],
    )
    assert_ok(rv)
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_2_id}/audit-board"
    )
    audit_boards = json.loads(rv.data)["auditBoards"]
    return [ab["id"] for ab in audit_boards]


# Add special routes to test our auth decorators. This fixture will run once before
# the test session starts. We have to add the route before starting any tests
# or else Flask complains. See test_auth.py for the tests that use these routes.
@pytest.fixture(scope="session", autouse=True)
def auth_decorator_test_routes():
    @app.route("/api/election/<election_id>/test_auth")
    @with_election_access
    def fake_election_route(election: Election):  # pylint: disable=unused-variable
        assert election
        return jsonify(election.id)

    @app.route("/api/election/<election_id>/jurisdiction/<jurisdiction_id>/test_auth")
    @with_jurisdiction_access
    def fake_jurisdiction_route(
        election: Election, jurisdiction: Jurisdiction
    ):  # pylint: disable=unused-variable
        assert election
        assert jurisdiction
        return jsonify([election.id, jurisdiction.id])

    @app.route(
        "/api/election/<election_id>/jurisdiction/<jurisdiction_id>/round/<round_id>/audit-board/<audit_board_id>/test_auth"
    )
    @with_audit_board_access
    def fake_audit_board_route(
        election: Election,
        jurisdiction: Jurisdiction,
        round: Round,
        audit_board: AuditBoard,
    ):  # pylint: disable=unused-variable
        assert election
        assert jurisdiction
        assert round
        assert audit_board
        return jsonify([election.id, jurisdiction.id, round.id, audit_board.id])


# Add special routes to test our error handlers. This fixture will run once before
# the test session starts. We have to add the route before starting any tests
# or else Flask complains. See test_errors.py for the tests that use these routes.
@pytest.fixture(scope="session", autouse=True)
def error_test_routes():
    @app.route("/test_uncaught_exception")
    def fake_uncaught_exception_route():  # pylint: disable=unused-variable
        raise Exception("Catch me if you can!")

    @app.route("/test_internal_error")
    def fake_internal_error_route():  # pylint: disable=unused-variable
        abort(500)
