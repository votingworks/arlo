import pytest
from sqlalchemy.exc import SQLAlchemyError
from flask.testing import FlaskClient

import json, io, uuid
from datetime import datetime
from typing import List

from tests.helpers import (
    assert_ok,
    put_json,
    post_json,
    compare_json,
    assert_is_date,
    asserts_startswith,
)
from arlo_server import db
from arlo_server.models import (
    AuditBoard,
    SampledBallot,
    SampledBallotDraw,
    USState,
)
from bgcompute import bgcompute_update_ballot_manifest_file


def test_jurisdictions_list_empty(client: FlaskClient, election_id: str):
    rv = client.get(f"/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)
    assert jurisdictions == {"jurisdictions": []}


def test_jurisdictions_list_no_manifest(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
):
    rv = client.get(f"/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)
    assert jurisdictions == {
        "jurisdictions": [
            {
                "id": jurisdiction_ids[0],
                "name": "J1",
                "ballotManifest": {
                    "file": None,
                    "processing": None,
                    "numBallots": None,
                    "numBatches": None,
                },
                "currentRoundStatus": None,
            },
            {
                "id": jurisdiction_ids[1],
                "name": "J2",
                "ballotManifest": {
                    "file": None,
                    "processing": None,
                    "numBallots": None,
                    "numBatches": None,
                },
                "currentRoundStatus": None,
            },
            {
                "id": jurisdiction_ids[2],
                "name": "J3",
                "ballotManifest": {
                    "file": None,
                    "processing": None,
                    "numBallots": None,
                    "numBatches": None,
                },
                "currentRoundStatus": None,
            },
        ]
    }


def test_jurisdictions_list_with_manifest(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
):
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
    assert bgcompute_update_ballot_manifest_file() == 1

    rv = client.get(f"/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)
    expected = {
        "jurisdictions": [
            {
                "id": jurisdiction_ids[0],
                "name": "J1",
                "ballotManifest": {
                    "file": {"name": "manifest.csv", "uploadedAt": assert_is_date},
                    "processing": {
                        "status": "PROCESSED",
                        "startedAt": assert_is_date,
                        "completedAt": assert_is_date,
                        "error": None,
                    },
                    "numBallots": 23 + 101 + 122 + 400,
                    "numBatches": 4,
                },
                "currentRoundStatus": None,
            },
            {
                "id": jurisdiction_ids[1],
                "name": "J2",
                "ballotManifest": {
                    "file": None,
                    "processing": None,
                    "numBallots": None,
                    "numBatches": None,
                },
                "currentRoundStatus": None,
            },
            {
                "id": jurisdiction_ids[2],
                "name": "J3",
                "ballotManifest": {
                    "file": None,
                    "processing": None,
                    "numBallots": None,
                    "numBatches": None,
                },
                "currentRoundStatus": None,
            },
        ]
    }
    compare_json(jurisdictions, expected)


def test_duplicate_batch_name(client, election_id, jurisdiction_ids):
    rv = client.put(
        f"/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/manifest",
        data={
            "manifest": (
                io.BytesIO(b"Batch Name,Number of Ballots\n" b"1,23\n" b"1,101\n"),
                "manifest.csv",
            )
        },
    )
    assert_ok(rv)

    with pytest.raises(SQLAlchemyError):
        bgcompute_update_ballot_manifest_file()

    db.session.rollback()

    rv = client.get(f"/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)
    expected = {
        "jurisdictions": [
            {
                "id": jurisdiction_ids[0],
                "name": "J1",
                "ballotManifest": {
                    "file": {"name": "manifest.csv", "uploadedAt": assert_is_date},
                    "processing": {
                        "status": "ERRORED",
                        "startedAt": assert_is_date,
                        "completedAt": assert_is_date,
                        "error": asserts_startswith(
                            '(psycopg2.errors.UniqueViolation) duplicate key value violates unique constraint "batch_jurisdiction_id_name_key"'
                        ),
                    },
                    "numBallots": None,
                    "numBatches": None,
                },
                "currentRoundStatus": None,
            },
            {
                "id": jurisdiction_ids[1],
                "name": "J2",
                "ballotManifest": {
                    "file": None,
                    "processing": None,
                    "numBallots": None,
                    "numBatches": None,
                },
                "currentRoundStatus": None,
            },
            {
                "id": jurisdiction_ids[2],
                "name": "J3",
                "ballotManifest": {
                    "file": None,
                    "processing": None,
                    "numBallots": None,
                    "numBatches": None,
                },
                "currentRoundStatus": None,
            },
        ]
    }
    compare_json(jurisdictions, expected)


def test_jurisdictions_round_status(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    contest_id: str,  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
):
    SAMPLE_SIZE = 119  # Bravo sample size
    J1_SAMPLES = 81  # Expected result of sampler for jurisdiction 1
    AB1_SAMPLES = 23  # Arbitrary num of ballots to assign to audit board 1

    rv = post_json(
        client,
        f"/election/{election_id}/round",
        {"roundNum": 1, "sampleSize": SAMPLE_SIZE},
    )
    assert_ok(rv)

    rv = client.get(f"/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]

    assert jurisdictions[0]["currentRoundStatus"] == {
        "status": "NOT_STARTED",
        "numBallotsSampled": J1_SAMPLES,
        "numBallotsAudited": 0,
    }
    assert jurisdictions[1]["currentRoundStatus"] == {
        "status": "NOT_STARTED",
        "numBallotsSampled": SAMPLE_SIZE - J1_SAMPLES,
        "numBallotsAudited": 0,
    }
    assert jurisdictions[2]["currentRoundStatus"] == {
        "status": "COMPLETE",
        "numBallotsSampled": 0,
        "numBallotsAudited": 0,
    }

    # Simulate creating some audit boards
    rv = client.get(f"/election/{election_id}/round")
    round = json.loads(rv.data)["rounds"][0]

    ballots = (
        SampledBallot.query.join(SampledBallotDraw)
        .filter_by(round_id=round["id"])
        .all()
    )
    audit_board_1 = AuditBoard(
        id=str(uuid.uuid4()),
        jurisdiction_id=jurisdiction_ids[0],
        round_id=round["id"],
        sampled_ballots=ballots[: AB1_SAMPLES + 1],
    )
    audit_board_2 = AuditBoard(
        id=str(uuid.uuid4()),
        jurisdiction_id=jurisdiction_ids[0],
        round_id=round["id"],
        sampled_ballots=ballots[AB1_SAMPLES + 1 :],
    )
    db.session.add(audit_board_1)
    db.session.add(audit_board_2)
    db.session.commit()

    rv = client.get(f"/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]

    assert jurisdictions[0]["currentRoundStatus"] == {
        "status": "IN_PROGRESS",
        "numBallotsSampled": J1_SAMPLES,
        "numBallotsAudited": 0,
    }
    assert jurisdictions[1]["currentRoundStatus"] == {
        "status": "NOT_STARTED",
        "numBallotsSampled": SAMPLE_SIZE - J1_SAMPLES,
        "numBallotsAudited": 0,
    }
    assert jurisdictions[2]["currentRoundStatus"] == {
        "status": "COMPLETE",
        "numBallotsSampled": 0,
        "numBallotsAudited": 0,
    }

    # Simulate one audit board auditing all its ballots and signing off
    audit_board_1 = db.session.merge(audit_board_1)  # Reload into the session
    for ballot in audit_board_1.sampled_ballots:
        ballot.vote = "YES"
    audit_board_1.signed_off_at = datetime.utcnow()
    db.session.commit()

    rv = client.get(f"/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]

    assert jurisdictions[0]["currentRoundStatus"] == {
        "status": "IN_PROGRESS",
        "numBallotsSampled": J1_SAMPLES,
        "numBallotsAudited": AB1_SAMPLES,
    }

    # Simulate the other audit board auditing all its ballots and signing off
    audit_board_2 = db.session.merge(audit_board_2)  # Reload into the session
    for ballot in audit_board_2.sampled_ballots:
        ballot.vote = "NO"
    audit_board_2.signed_off_at = datetime.utcnow()
    db.session.commit()

    rv = client.get(f"/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]

    assert jurisdictions[0]["currentRoundStatus"] == {
        "status": "COMPLETE",
        "numBallotsSampled": J1_SAMPLES,
        "numBallotsAudited": J1_SAMPLES,
    }


def test_jurisdictions_round_status_offline(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    contest_id: str,  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
):
    SAMPLE_SIZE = 119  # Bravo sample size
    J1_SAMPLES = 81  # Expected result of sampler for jurisdiction 1
    AB1_SAMPLES = 23  # Arbitrary num of ballots to assign to audit board 1

    # Change the settings to offline
    settings = {
        "electionName": "Test Election",
        "online": False,
        "randomSeed": "1234567890",
        "riskLimit": 10,
        "state": USState.California,
    }
    rv = put_json(client, f"/election/{election_id}/settings", settings)
    assert_ok(rv)

    rv = post_json(
        client,
        f"/election/{election_id}/round",
        {"roundNum": 1, "sampleSize": SAMPLE_SIZE},
    )
    assert_ok(rv)

    rv = client.get(f"/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]

    assert jurisdictions[0]["currentRoundStatus"] == {
        "status": "NOT_STARTED",
        "numBallotsSampled": J1_SAMPLES,
        "numBallotsAudited": 0,
    }

    # Simulate creating an audit board
    rv = client.get(f"/election/{election_id}/round")
    round = json.loads(rv.data)["rounds"][0]

    ballots = (
        SampledBallot.query.join(SampledBallotDraw)
        .filter_by(round_id=round["id"])
        .all()
    )
    audit_board_1 = AuditBoard(
        id=str(uuid.uuid4()),
        jurisdiction_id=jurisdiction_ids[0],
        round_id=round["id"],
        sampled_ballots=ballots[: AB1_SAMPLES + 1],
    )
    db.session.add(audit_board_1)
    db.session.commit()

    rv = client.get(f"/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]

    assert jurisdictions[0]["currentRoundStatus"] == {
        "status": "IN_PROGRESS",
        "numBallotsSampled": J1_SAMPLES,
        "numBallotsAudited": 0,
    }

    # Simulate the audit board signing off
    audit_board_1 = db.session.merge(audit_board_1)  # Reload into the session
    audit_board_1.signed_off_at = datetime.utcnow()
    db.session.commit()

    rv = client.get(f"/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]

    assert jurisdictions[0]["currentRoundStatus"] == {
        "status": "COMPLETE",
        "numBallotsSampled": J1_SAMPLES,
        "numBallotsAudited": J1_SAMPLES,
    }
