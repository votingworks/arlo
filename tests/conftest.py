import pytest
from flask.testing import FlaskClient
import io, uuid, json
from datetime import datetime
from typing import List, Generator
from flask import jsonify

from arlo_server import app, db
from arlo_server.models import (
    Election,
    Jurisdiction,
    USState,
    Round,
    RoundContestResult,
    Contest,
)
from arlo_server.auth import with_election_access, with_jurisdiction_access, UserType
from tests.helpers import (
    assert_ok,
    put_json,
    post_json,
    create_election,
    create_jurisdiction_admin,
    set_logged_in_user,
    DEFAULT_JA_EMAIL,
)
from bgcompute import (
    bgcompute_update_election_jurisdictions_file,
    bgcompute_update_ballot_manifest_file,
)


# The fixtures in this module are available in any test via dependency
# injection.

SAMPLE_SIZE = 119  # Bravo sample size for round 1


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
def election_id(client: FlaskClient) -> Generator[str, None, None]:
    yield create_election(client)


@pytest.fixture
def jurisdiction_ids(
    client: FlaskClient, election_id: str
) -> Generator[List[str], None, None]:
    # We expect the API to order the jurisdictions by name, so we upload them
    # out of order.
    rv = client.put(
        f"/election/{election_id}/jurisdiction/file",
        data={
            "jurisdictions": (
                io.BytesIO(
                    b"Jurisdiction,Admin Email\n"
                    b"J2,a2@example.com\n"
                    b"J3,a3@example.com\n"
                    b"J1,a1@example.com"
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
    yield [j.id for j in jurisdictions]


@pytest.fixture
def contest_id(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
) -> Generator[str, None, None]:
    contest_id = str(uuid.uuid4())
    contest = {
        "id": contest_id,
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
    }
    rv = put_json(client, f"/election/{election_id}/contest", [contest])
    assert_ok(rv)
    yield contest_id


@pytest.fixture
def election_settings(client: FlaskClient, election_id: str) -> None:
    settings = {
        "electionName": "Test Election",
        "online": True,
        "randomSeed": "1234567890",
        "riskLimit": 10,
        "state": USState.California,
    }
    rv = put_json(client, f"/election/{election_id}/settings", settings)
    assert_ok(rv)


@pytest.fixture
def manifests(client: FlaskClient, election_id: str, jurisdiction_ids: List[str]):
    rv = client.put(
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/manifest",
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
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/manifest",
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
    contest_id: str,  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
) -> Generator[str, None, None]:
    rv = post_json(
        client,
        f"/election/{election_id}/round",
        {"roundNum": 1, "sampleSize": SAMPLE_SIZE},
    )
    assert_ok(rv)
    rv = client.get(f"/election/{election_id}/round",)
    rounds = json.loads(rv.data)["rounds"]
    yield rounds[0]["id"]


@pytest.fixture
def round_2_id(
    client: FlaskClient,
    election_id: str,
    contest_id: str,
    round_1_id: str,
    audit_board_round_1_ids: List[str],  # pylint: disable=unused-argument
) -> Generator[str, None, None]:
    # Fake that the first round got completed by setting Round.ended_at.
    # We also need to add RoundContestResults so that the next round sample
    # size can get computed.
    round = Round.query.get(round_1_id)
    round.ended_at = datetime.utcnow()
    contest = Contest.query.get(contest_id)
    db.session.add(
        RoundContestResult(
            round_id=round.id,
            contest_id=contest.id,
            contest_choice_id=contest.choices[0].id,
            result=70,
        )
    )
    db.session.add(
        RoundContestResult(
            round_id=round.id,
            contest_id=contest.id,
            contest_choice_id=contest.choices[1].id,
            result=49,
        )
    )
    db.session.commit()

    rv = post_json(client, f"/election/{election_id}/round", {"roundNum": 2},)
    assert_ok(rv)

    rv = client.get(f"/election/{election_id}/round",)
    rounds = json.loads(rv.data)["rounds"]
    yield rounds[1]["id"]


@pytest.fixture
def audit_board_round_1_ids(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: str,
    round_1_id: str,
    as_jurisdiction_admin,  # pylint: disable=unused-argument
) -> Generator[List[str], None, None]:
    rv = post_json(
        client,
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
        [{"name": "Audit Board #1"}, {"name": "Audit Board #2"}],
    )
    assert_ok(rv)
    rv = client.get(
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board"
    )
    audit_boards = json.loads(rv.data)["auditBoards"]
    yield [ab["id"] for ab in audit_boards]


@pytest.fixture
def audit_board_round_2_ids(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: str,
    round_2_id: str,
    as_jurisdiction_admin,  # pylint: disable=unused-argument
) -> Generator[List[str], None, None]:
    rv = post_json(
        client,
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_2_id}/audit-board",
        [
            {"name": "Audit Board #1"},
            {"name": "Audit Board #2"},
            {"name": "Audit Board #3"},
        ],
    )
    assert_ok(rv)
    rv = client.get(
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_2_id}/audit-board"
    )
    audit_boards = json.loads(rv.data)["auditBoards"]
    yield [ab["id"] for ab in audit_boards]


@pytest.fixture
def as_jurisdiction_admin(client: FlaskClient, jurisdiction_ids: List[str]):
    create_jurisdiction_admin(jurisdiction_ids[0])
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)


# Add special routes to test our auth decorators. This fixture will run once before
# the test session starts. We have to add the route before starting any tests
# or else Flask complains. See test_auth.py for the tests that use these routes.
@pytest.fixture(scope="session", autouse=True)
def auth_decorator_test_routes():
    @app.route("/election/<election_id>/test_auth")
    @with_election_access
    def fake_election_route(election: Election):
        assert election
        return jsonify(election.id)

    @app.route("/election/<election_id>/jurisdiction/<jurisdiction_id>/test_auth")
    @with_jurisdiction_access
    def fake_jurisdiction_route(election: Election, jurisdiction: Jurisdiction):
        assert election
        assert jurisdiction
        return jsonify([election.id, jurisdiction.id])
