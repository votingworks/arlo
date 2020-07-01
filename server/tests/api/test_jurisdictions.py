import json, io, uuid
from datetime import datetime
from typing import List
from flask.testing import FlaskClient

from ..helpers import (
    assert_ok,
    put_json,
    post_json,
    compare_json,
    assert_is_date,
    set_logged_in_user,
    DEFAULT_JA_EMAIL,
    SAMPLE_SIZE_ROUND_1,
    J1_SAMPLES_ROUND_1,
    J1_BALLOTS_ROUND_1,
    BALLOTS_ROUND_1,
    AB1_SAMPLES_ROUND_1,
    AB1_BALLOTS_ROUND_1,
)
from ...auth import UserType
from ...database import db_session
from ...models import *  # pylint: disable=wildcard-import
from ...bgcompute import bgcompute_update_ballot_manifest_file

AB1_SAMPLES = 23  # Arbitrary num of ballots to assign to audit board 1


def test_jurisdictions_list_empty(client: FlaskClient, election_id: str):
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)
    assert jurisdictions == {"jurisdictions": []}


def test_jurisdictions_list_no_manifest(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
):
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
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
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    manifest = (
        b"Batch Name,Number of Ballots\n" b"1,23\n" b"2,101\n" b"3,122\n" b"4,400"
    )
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest",
        data={"manifest": (io.BytesIO(manifest), "manifest.csv",)},
    )
    assert_ok(rv)
    assert bgcompute_update_ballot_manifest_file() == 1

    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)
    expected = {
        "jurisdictions": [
            {
                "id": jurisdiction_ids[0],
                "name": "J1",
                "ballotManifest": {
                    "file": {"name": "manifest.csv", "uploadedAt": assert_is_date,},
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

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest/csv"
    )
    assert rv.headers["Content-Disposition"] == 'attachment; filename="manifest.csv"'
    assert rv.data == manifest


def test_download_ballot_manifest_not_found(client, election_id, jurisdiction_ids):
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest/csv"
    )
    assert rv.status_code == 404


def test_duplicate_batch_name(client, election_id, jurisdiction_ids):
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, DEFAULT_JA_EMAIL)
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest",
        data={
            "manifest": (
                io.BytesIO(b"Batch Name,Number of Ballots\n" b"1,23\n" b"1,101\n"),
                "manifest.csv",
            )
        },
    )
    assert_ok(rv)

    bgcompute_update_ballot_manifest_file()

    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)
    expected = {
        "jurisdictions": [
            {
                "id": jurisdiction_ids[0],
                "name": "J1",
                "ballotManifest": {
                    "file": {"name": "manifest.csv", "uploadedAt": assert_is_date,},
                    "processing": {
                        "status": "ERRORED",
                        "startedAt": assert_is_date,
                        "completedAt": assert_is_date,
                        "error": "Values in column Batch Name must be unique. Found duplicate value: 1.",
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


def test_jurisdictions_status_round_1_no_audit_boards(
    client: FlaskClient,
    election_id: str,
    round_1_id: str,  # pylint: disable=unused-argument
):
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]

    assert jurisdictions[0]["currentRoundStatus"] == {
        "status": "NOT_STARTED",
        "numSamples": J1_SAMPLES_ROUND_1,
        "numSamplesAudited": 0,
        "numBallots": J1_BALLOTS_ROUND_1,
        "numBallotsAudited": 0,
    }
    assert jurisdictions[1]["currentRoundStatus"] == {
        "status": "NOT_STARTED",
        "numSamples": SAMPLE_SIZE_ROUND_1 - J1_SAMPLES_ROUND_1,
        "numSamplesAudited": 0,
        "numBallots": BALLOTS_ROUND_1 - J1_BALLOTS_ROUND_1,
        "numBallotsAudited": 0,
    }
    assert jurisdictions[2]["currentRoundStatus"] == {
        "status": "COMPLETE",
        "numSamples": 0,
        "numSamplesAudited": 0,
        "numBallots": 0,
        "numBallotsAudited": 0,
    }


def test_jurisdictions_status_round_1_with_audit_boards(
    client: FlaskClient, election_id: str, audit_board_round_1_ids: List[str],
):
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]

    assert jurisdictions[0]["currentRoundStatus"] == {
        "status": "IN_PROGRESS",
        "numSamples": J1_SAMPLES_ROUND_1,
        "numSamplesAudited": 0,
        "numBallots": J1_BALLOTS_ROUND_1,
        "numBallotsAudited": 0,
    }
    assert jurisdictions[1]["currentRoundStatus"] == {
        "status": "NOT_STARTED",
        "numSamples": SAMPLE_SIZE_ROUND_1 - J1_SAMPLES_ROUND_1,
        "numSamplesAudited": 0,
        "numBallots": BALLOTS_ROUND_1 - J1_BALLOTS_ROUND_1,
        "numBallotsAudited": 0,
    }
    assert jurisdictions[2]["currentRoundStatus"] == {
        "status": "COMPLETE",
        "numSamples": 0,
        "numSamplesAudited": 0,
        "numBallots": 0,
        "numBallotsAudited": 0,
    }

    # Simulate one audit board auditing all its ballots and signing off
    audit_board_1 = AuditBoard.query.get(audit_board_round_1_ids[0])
    for ballot in audit_board_1.sampled_ballots:
        ballot.status = BallotStatus.AUDITED
    audit_board_1.signed_off_at = datetime.utcnow()
    db_session.commit()

    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]

    assert jurisdictions[0]["currentRoundStatus"] == {
        "status": "IN_PROGRESS",
        "numSamples": J1_SAMPLES_ROUND_1,
        "numSamplesAudited": AB1_SAMPLES_ROUND_1,
        "numBallots": J1_BALLOTS_ROUND_1,
        "numBallotsAudited": AB1_BALLOTS_ROUND_1,
    }

    # Simulate the other audit board auditing all its ballots and signing off
    audit_board_2 = AuditBoard.query.get(audit_board_round_1_ids[1])
    for ballot in audit_board_2.sampled_ballots:
        ballot.status = BallotStatus.AUDITED
    audit_board_2.signed_off_at = datetime.utcnow()
    db_session.commit()

    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]

    assert jurisdictions[0]["currentRoundStatus"] == {
        "status": "COMPLETE",
        "numSamples": J1_SAMPLES_ROUND_1,
        "numSamplesAudited": J1_SAMPLES_ROUND_1,
        "numBallots": J1_BALLOTS_ROUND_1,
        "numBallotsAudited": J1_BALLOTS_ROUND_1,
    }


def test_jurisdictions_round_status_offline(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: List[str],  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
):
    # Change the settings to offline
    settings = {
        "electionName": "Test Election",
        "online": False,
        "randomSeed": "1234567890",
        "riskLimit": 10,
        "state": USState.California,
    }
    rv = put_json(client, f"/api/election/{election_id}/settings", settings)
    assert_ok(rv)

    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {"roundNum": 1, "sampleSize": SAMPLE_SIZE_ROUND_1},
    )
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]

    assert jurisdictions[0]["currentRoundStatus"] == {
        "status": "NOT_STARTED",
        "numSamples": J1_SAMPLES_ROUND_1,
        "numSamplesAudited": 0,
        "numBallots": J1_BALLOTS_ROUND_1,
        "numBallotsAudited": 0,
    }

    # Simulate creating an audit board
    rv = client.get(f"/api/election/{election_id}/round")
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
    db_session.add(audit_board_1)
    db_session.commit()

    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]

    assert jurisdictions[0]["currentRoundStatus"] == {
        "status": "IN_PROGRESS",
        "numSamples": J1_SAMPLES_ROUND_1,
        "numSamplesAudited": 0,
        "numBallots": J1_BALLOTS_ROUND_1,
        "numBallotsAudited": 0,
    }

    # Simulate the audit board signing off
    audit_board_1 = db_session.merge(audit_board_1)  # Reload into the session
    audit_board_1.signed_off_at = datetime.utcnow()
    db_session.commit()

    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]

    assert jurisdictions[0]["currentRoundStatus"] == {
        "status": "COMPLETE",
        "numSamples": J1_SAMPLES_ROUND_1,
        "numSamplesAudited": J1_SAMPLES_ROUND_1,
        "numBallots": J1_BALLOTS_ROUND_1,
        "numBallotsAudited": J1_BALLOTS_ROUND_1,
    }
