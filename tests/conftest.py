import pytest
from flask.testing import FlaskClient
import io, uuid, json
from datetime import datetime
from typing import List, Generator
from flask import jsonify
from sqlalchemy.orm import joinedload

from arlo_server import app, db
from arlo_server.models import (
    Election,
    Jurisdiction,
    USState,
    Round,
    RoundContestResult,
    Contest,
    SampledBallotDraw,
    AuditBoard,
)
from arlo_server.auth import (
    UserType,
    with_election_access,
    with_jurisdiction_access,
    with_audit_board_access,
)
from tests.helpers import (
    assert_ok,
    put_json,
    post_json,
    create_election,
    set_logged_in_user,
    DEFAULT_JA_EMAIL,
    DEFAULT_AA_EMAIL,
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
    rv = client.put(
        f"/election/{election_id}/jurisdiction/file",
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
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = client.put(
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest",
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
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/ballot-manifest",
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
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
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
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)

    # Fake that the first round got completed by:
    # - auditing all the sampled ballots
    # - setting Round.ended_at
    # - add RoundContestResults
    WINNER_VOTES = 70
    round = Round.query.options(
        joinedload(Round.sampled_ballot_draws).joinedload(
            SampledBallotDraw.sampled_ballot
        )
    ).get(round_1_id)
    contest = Contest.query.get(contest_id)
    for ballot_draw in round.sampled_ballot_draws[:WINNER_VOTES]:
        ballot_draw.sampled_ballot.vote = contest.choices[0].id
    for ballot_draw in round.sampled_ballot_draws[WINNER_VOTES:]:
        ballot_draw.sampled_ballot.vote = contest.choices[1].id
    round.ended_at = datetime.utcnow()
    db.session.add(
        RoundContestResult(
            round_id=round.id,
            contest_id=contest.id,
            contest_choice_id=contest.choices[0].id,
            result=WINNER_VOTES,
        )
    )
    db.session.add(
        RoundContestResult(
            round_id=round.id,
            contest_id=contest.id,
            contest_choice_id=contest.choices[1].id,
            result=SAMPLE_SIZE - WINNER_VOTES,
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
    client: FlaskClient, election_id: str, jurisdiction_ids: str, round_1_id: str,
) -> Generator[List[str], None, None]:
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
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
    client: FlaskClient, election_id: str, jurisdiction_ids: str, round_2_id: str,
) -> Generator[List[str], None, None]:
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
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

    @app.route(
        "/election/<election_id>/jurisdiction/<jurisdiction_id>/round/<round_id>/audit-board/<audit_board_id>/test_auth"
    )
    @with_audit_board_access
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
