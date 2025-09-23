import io
import uuid
import json
import os
from typing import List
from flask.testing import FlaskClient
from flask import jsonify, abort
import pytest
from filelock import FileLock
from unittest.mock import Mock, patch

# Before we set up the Flask app, set the env. That way it will use the test
# config and we can still run tests without setting the env var manually.
os.environ["FLASK_ENV"] = "test"
# In testing, we run background tasks immediately, since we'll only be doing
# small tasks and we want to make sure they run in a thread-safe way (i.e. we
# don't want tests to interfere with each other's background tasks when running
# concurrently).
os.environ["RUN_BACKGROUND_TASKS_IMMEDIATELY"] = "True"
# Always use the local file system (not S3) for tests.
os.environ["ARLO_FILE_UPLOAD_STORAGE_PATH"] = "/tmp/arlo-test"


from ..app import app
from ..database import reset_db
from ..models import *
from ..auth import UserType, restrict_access
from .helpers import *


# Mock OpenID Connect Discovery endpoints for OAuth
def mock_openid_configuration_response(method: str, url: str, **kwargs) -> Mock:
    """Mock response for OpenID Connect Discovery document requests"""
    if url.endswith("/.well-known/openid-configuration"):
        base_url = url.replace("/.well-known/openid-configuration", "")
        # Mock OpenID Connect Discovery document
        discovery_doc = {
            "issuer": base_url,
            "authorization_endpoint": f"{base_url}/authorize",
            "token_endpoint": f"{base_url}/oauth/token",
            "userinfo_endpoint": f"{base_url}/userinfo",
            "jwks_uri": f"{base_url}/.well-known/jwks.json",
            "scopes_supported": ["openid", "profile", "email"],
            "response_types_supported": ["code"],
            "grant_types_supported": ["authorization_code"],
            "subject_types_supported": ["public"],
            "id_token_signing_alg_values_supported": ["RS256"],
        }
        response = Mock()
        response.json.return_value = discovery_doc
        response.status_code = 200
        response.headers = {"Content-Type": "application/json"}
        return response

    # For any other URL, raise an exception to catch unexpected requests
    raise Exception(f"Unexpected request to {url}")


# Apply the mock to requests.Session.request for all tests
@pytest.fixture(scope="session", autouse=True)
def mock_oauth_requests():
    with patch(
        "requests.Session.request", side_effect=mock_openid_configuration_response
    ):
        yield


# The fixtures in this module are available in any test via dependency
# injection.


# Reset the db once per test session. This means that every test will operate
# with a shared db, which better simulates the real world.
# Based on https://github.com/pytest-dev/pytest-xdist#making-session-scoped-fixtures-execute-only-once
@pytest.fixture(scope="session", autouse=True)
def reset_test_db(tmp_path_factory, worker_id):
    # If we're not executing with multiple workers (from pytest-xdist), simply
    # reset the db.
    if worker_id == "master":
        reset_db()
        return

    # Otherwise, use a file lock in a temp directory shared by all workers to
    # ensure only one worker can reset the db.
    root_tmp_dir = tmp_path_factory.getbasetemp().parent
    temp_file = root_tmp_dir / "reset_db"
    with FileLock(str(temp_file) + ".lock"):
        if not temp_file.is_file():
            reset_db()
            temp_file.write_text("reset_db complete")


@pytest.fixture
def client() -> FlaskClient:
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture
def org_id(client: FlaskClient, request) -> str:
    org_id, _ = create_org_and_admin(f"Test Org {request.node.name}", DEFAULT_AA_EMAIL)
    return org_id


@pytest.fixture
def election_id(client: FlaskClient, org_id: str, request) -> str:
    set_logged_in_user(client, UserType.AUDIT_ADMIN, user_key=DEFAULT_AA_EMAIL)
    return create_election(
        client, audit_name=f"Test Audit {request.node.name}", organization_id=org_id
    )


@pytest.fixture
def jurisdiction_ids(client: FlaskClient, election_id: str) -> List[str]:
    rv = upload_jurisdictions_file(
        client,
        # We expect the API to order the jurisdictions by name, so we
        # upload them out of order.
        io.BytesIO(
            (
                "Jurisdiction,Admin Email\n"
                f"J2,{default_ja_email(election_id)}\n"
                f"J3,j3-{election_id}@example.com\n"
                f"J1,{default_ja_email(election_id)}\n"
            ).encode()
        ),
        election_id,
    )
    assert_ok(rv)

    jurisdictions = (
        Jurisdiction.query.filter_by(election_id=election_id)
        .order_by(Jurisdiction.name)
        .all()
    )

    # verify jurisdictions processed correctly
    assert len(jurisdictions) == 3
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
                {
                    "id": str(uuid.uuid4()),
                    "name": "candidate 1",
                    "numVotes": 600,
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "candidate 2",
                    "numVotes": 400,
                },
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
                {
                    "id": str(uuid.uuid4()),
                    "name": "candidate 1",
                    "numVotes": 200,
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "candidate 2",
                    "numVotes": 300,
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "candidate 3",
                    "numVotes": 100,
                },
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
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
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
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = upload_ballot_manifest(
        client,
        io.BytesIO(b"Batch Name,Number of Ballots\n1,23\n2,101\n3,122\n4,400"),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)
    rv = upload_ballot_manifest(
        client,
        io.BytesIO(b"Batch Name,Number of Ballots\n1,20\n2,10\n3,220\n4,40"),
        election_id,
        jurisdiction_ids[1],
    )
    assert_ok(rv)


@pytest.fixture
def round_1_id(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: str,
    election_settings,
    manifests,
) -> str:
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/sample-sizes/1")
    sample_size_options = json.loads(rv.data)["sampleSizes"]
    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {
            "roundNum": 1,
            "sampleSizes": {contest_ids[0]: sample_size_options[contest_ids[0]][0]},
        },
    )
    assert_ok(rv)
    rv = client.get(
        f"/api/election/{election_id}/round",
    )
    rounds = json.loads(rv.data)["rounds"]
    return str(rounds[0]["id"])


@pytest.fixture
def round_2_id(
    client: FlaskClient,
    election_id: str,
    contest_ids: List[str],
    round_1_id: str,
    audit_board_round_1_ids: List[str],
) -> str:
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    run_audit_round(round_1_id, contest_ids[0], contest_ids, 0.55)

    rv = client.post(f"/api/election/{election_id}/round/current/finish")
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/sample-sizes/2")
    sample_size_options = json.loads(rv.data)["sampleSizes"]

    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {
            "roundNum": 2,
            "sampleSizes": {
                contest_id: options[0]
                for contest_id, options in sample_size_options.items()
            },
        },
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/round",
    )
    rounds = json.loads(rv.data)["rounds"]
    return str(rounds[1]["id"])


@pytest.fixture
def audit_board_round_1_ids(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: str,
    round_1_id: str,
) -> List[str]:
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
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
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: str,
    round_2_id: str,
) -> List[str]:
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
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
    @restrict_access([UserType.AUDIT_ADMIN])
    def fake_election_route(election: Election):
        assert election
        return jsonify(election.id)

    @app.route("/api/election/<election_id>/jurisdiction/<jurisdiction_id>/test_auth")
    @restrict_access([UserType.AUDIT_ADMIN, UserType.JURISDICTION_ADMIN])
    def fake_jurisdiction_route(election: Election, jurisdiction: Jurisdiction):
        assert election
        assert jurisdiction
        return jsonify([election.id, jurisdiction.id])

    @app.route(
        "/api/election/<election_id>/jurisdiction/<jurisdiction_id>/round/<round_id>/audit-board/<audit_board_id>/test_auth"
    )
    @restrict_access([UserType.AUDIT_BOARD])
    def fake_audit_board_route(
        election: Election,
        jurisdiction: Jurisdiction,
        round: Round,
        audit_board: AuditBoard,
    ):
        assert election
        assert jurisdiction
        assert round
        assert audit_board
        return jsonify([election.id, jurisdiction.id, round.id, audit_board.id])

    @app.route(
        "/api/election/<election_id>/jurisdiction/<jurisdiction_id>/tally-entry/test_auth"
    )
    @restrict_access([UserType.TALLY_ENTRY])
    def fake_tally_entry_route(election: Election, jurisdiction: Jurisdiction):
        assert election
        assert jurisdiction
        return jsonify([election.id, jurisdiction.id])


# Add special routes to test our error handlers. This fixture will run once before
# the test session starts. We have to add the route before starting any tests
# or else Flask complains. See test_errors.py for the tests that use these routes.
@pytest.fixture(scope="session", autouse=True)
def error_test_routes():
    @app.route("/test_uncaught_exception")
    def fake_uncaught_exception_route():
        raise Exception("Catch me if you can!")

    @app.route("/test_internal_error")
    def fake_internal_error_route():
        abort(500)
