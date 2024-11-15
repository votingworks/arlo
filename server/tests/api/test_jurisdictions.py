import json, io
from datetime import datetime, timedelta
from typing import List
from flask.testing import FlaskClient

from ...activity_log.activity_log import (
    ActivityBase,
    JurisdictionAdminLogin,
    record_activity,
)
from ...auth.auth_routes import record_login
from ..helpers import *  # pylint: disable=wildcard-import
from ...auth import UserType
from ...database import db_session
from ...models import *  # pylint: disable=wildcard-import

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
                "expectedBallotManifestNumBallots": None,
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
                "expectedBallotManifestNumBallots": None,
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
                "expectedBallotManifestNumBallots": None,
                "currentRoundStatus": None,
            },
        ]
    }


def test_jurisdictions_list_with_manifest(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    manifest = (
        b"Batch Name,Number of Ballots\n" b"1,23\n" b"2,101\n" b"3,122\n" b"4,400"
    )
    rv = upload_ballot_manifest(
        client,
        io.BytesIO(manifest),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)
    expected = {
        "jurisdictions": [
            {
                "id": jurisdiction_ids[0],
                "name": "J1",
                "ballotManifest": {
                    "file": {
                        "name": asserts_startswith("manifest"),
                        "uploadedAt": assert_is_date,
                    },
                    "processing": {
                        "status": "PROCESSED",
                        "startedAt": assert_is_date,
                        "completedAt": assert_is_date,
                        "error": None,
                    },
                    "numBallots": 23 + 101 + 122 + 400,
                    "numBatches": 4,
                },
                "expectedBallotManifestNumBallots": None,
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
                "expectedBallotManifestNumBallots": None,
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
                "expectedBallotManifestNumBallots": None,
                "currentRoundStatus": None,
            },
        ]
    }
    compare_json(jurisdictions, expected)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest/csv"
    )
    assert rv.headers["Content-Disposition"].startswith(
        'attachment; filename="manifest'
    )
    assert rv.data == manifest


def test_download_ballot_manifest_not_found(client, election_id, jurisdiction_ids):
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest/csv"
    )
    assert rv.status_code == 404


def test_duplicate_batch_name(client, election_id, jurisdiction_ids):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = upload_ballot_manifest(
        client,
        io.BytesIO(b"Batch Name,Number of Ballots\n" b"1,23\n" b"1,101\n"),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)
    expected = {
        "jurisdictions": [
            {
                "id": jurisdiction_ids[0],
                "name": "J1",
                "ballotManifest": {
                    "file": {
                        "name": asserts_startswith("manifest"),
                        "uploadedAt": assert_is_date,
                    },
                    "processing": {
                        "status": "ERRORED",
                        "startedAt": assert_is_date,
                        "completedAt": assert_is_date,
                        "error": "Each row must be uniquely identified by Batch Name. Found duplicate: 1.",
                    },
                    "numBallots": None,
                    "numBatches": None,
                },
                "expectedBallotManifestNumBallots": None,
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
                "expectedBallotManifestNumBallots": None,
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
                "expectedBallotManifestNumBallots": None,
                "currentRoundStatus": None,
            },
        ]
    }
    compare_json(jurisdictions, expected)


def test_jurisdictions_status_round_1_no_audit_boards(
    client: FlaskClient,
    election_id: str,
    round_1_id: str,  # pylint: disable=unused-argument
    snapshot,
):
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]

    snapshot.assert_match(
        [
            {
                "name": jurisdiction["name"],
                "currentRoundStatus": jurisdiction["currentRoundStatus"],
            }
            for jurisdiction in jurisdictions
        ]
    )


def test_jurisdictions_status_round_1_with_audit_boards(
    client: FlaskClient,
    election_id: str,
    audit_board_round_1_ids: List[str],
    snapshot,
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]

    snapshot.assert_match(
        [
            {
                "name": jurisdiction["name"],
                "currentRoundStatus": jurisdiction["currentRoundStatus"],
            }
            for jurisdiction in jurisdictions
        ]
    )

    # Simulate one audit board auditing all its ballots and signing off
    audit_board_1 = AuditBoard.query.get(audit_board_round_1_ids[0])
    for ballot in audit_board_1.sampled_ballots:
        ballot.status = BallotStatus.AUDITED
    audit_board_1.signed_off_at = datetime.now(timezone.utc)
    db_session.commit()

    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]

    snapshot.assert_match(jurisdictions[0]["currentRoundStatus"])

    # Simulate the other audit board auditing all its ballots and signing off
    audit_board_2 = AuditBoard.query.get(audit_board_round_1_ids[1])
    for ballot in audit_board_2.sampled_ballots:
        ballot.status = BallotStatus.AUDITED
    audit_board_2.signed_off_at = datetime.now(timezone.utc)
    db_session.commit()

    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]

    snapshot.assert_match(jurisdictions[0]["currentRoundStatus"])


def test_jurisdictions_status_round_1_with_audit_boards_without_ballots(
    client: FlaskClient,
    election_id: str,
    audit_board_round_1_ids: List[str],
):
    # Unassign all ballots for one audit board. This audit board shouldn't
    # factor into the jurisdiction's status
    SampledBallot.query.filter_by(audit_board_id=audit_board_round_1_ids[0]).delete()
    db_session.commit()

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]
    assert jurisdictions[0]["currentRoundStatus"]["status"] == "IN_PROGRESS"

    # Simulate the other audit board auditing all its ballots and signing off
    audit_board_2 = AuditBoard.query.get(audit_board_round_1_ids[1])
    for ballot in audit_board_2.sampled_ballots:
        ballot.status = BallotStatus.AUDITED
    audit_board_2.signed_off_at = datetime.now(timezone.utc)
    db_session.commit()

    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]
    assert jurisdictions[0]["currentRoundStatus"]["status"] == "COMPLETE"


def test_jurisdictions_round_status_offline(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: List[str],
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    snapshot,
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
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

    rv = client.get(f"/api/election/{election_id}/round")
    round_id = json.loads(rv.data)["rounds"][0]["id"]

    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]

    snapshot.assert_match(jurisdictions[0]["currentRoundStatus"])

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_id}/audit-board",
        [{"name": "Audit Board #1"}, {"name": "Audit Board #2"}],
    )

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)

    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]

    snapshot.assert_match(jurisdictions[0]["currentRoundStatus"])

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_id}/results",
    )
    assert rv.status_code == 200
    empty_results = json.loads(rv.data)

    full_results = {
        contest_id: {choice_id: 1 for choice_id in contest_results}
        for contest_id, contest_results in empty_results.items()
    }

    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_id}/results",
        full_results,
    )
    assert_ok(rv)

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)

    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]

    snapshot.assert_match(jurisdictions[0]["currentRoundStatus"])


def test_discrepancy_before_audit_launch(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
):
    rv = client.get(f"/api/election/{election_id}/discrepancy")
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Conflict",
                "message": "Audit not started",
            }
        ]
    }


def test_discrepancy_non_batch_comparison_enabled(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    round_1_id: str,  # pylint: disable=unused-argument
):
    rv = client.get(f"/api/election/{election_id}/discrepancy")
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Conflict",
                "message": "Discrepancies are only implemented for batch and ballot comparison audits",
            }
        ]
    }


def test_last_login_by_jurisdiction_with_round(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: str,
):
    # J3 has a unique JM which makes this test simpler
    jurisdiction_id = jurisdiction_ids[2]
    jurisdiction = Jurisdiction.query.filter_by(id=jurisdiction_id).one()
    user = User.query.filter(User.jurisdictions.any(id=jurisdiction_id)).one()

    # Log in before round starts
    record_login(user)

    # Should be able to see the login event
    def assert_login_event():
        rv = client.get(f"/api/election/{election_id}/jurisdictions/last-login")
        logins = json.loads(rv.data)

        expectation = {}
        expectation[jurisdiction.id] = {
            "activityName": "JurisdictionAdminLogin",
            "election": None,
            "id": assert_is_id,
            "info": {"error": None},
            "timestamp": assert_is_date,
            "user": {
                "key": asserts_startswith("j3"),
                "supportUser": None,
                "type": "jurisdiction_admin",
            },
        }
        compare_json(logins, {"lastLoginByJurisdiction": expectation})

    assert_login_event()

    # Start the audit
    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {
            "roundNum": 1,
            "sampleSizes": {contest_ids[0]: {"size": 100, "key": "0.7", "prob": 1}},
        },
    )
    assert_ok(rv)

    # Should no longer be able to see the login event because it happened before round start
    rv = client.get(f"/api/election/{election_id}/jurisdictions/last-login")
    logins = json.loads(rv.data)
    assert logins == {"lastLoginByJurisdiction": {}}

    # Log in after round start
    record_login(user)
    # Should be able to see the latest event
    assert_login_event()


def test_last_login_by_jurisdiction_most_recent(client: FlaskClient, election_id: str):
    rv = upload_jurisdictions_file(
        client,
        io.BytesIO(b"Jurisdiction,Admin Email\nJ1,a1@example.com\nJ1,a2@example.com"),
        election_id,
    )
    assert_ok(rv)

    election = Election.query.filter_by(id=election_id).one()
    assert [j.name for j in election.jurisdictions] == ["J1"]

    jurisdiction = election.jurisdictions[0]
    assert [a.user.email for a in jurisdiction.jurisdiction_administrations] == [
        "a1@example.com",
        "a2@example.com",
    ]

    user_1 = User.query.filter_by(email="a1@example.com").one()
    user_2 = User.query.filter_by(email="a2@example.com").one()

    organization = list(user_1.jurisdictions)[0].election.organization
    record_activity(
        JurisdictionAdminLogin(
            timestamp=datetime.now(timezone.utc) - timedelta(hours=0, minutes=5),
            base=ActivityBase(
                organization_id=organization.id,
                organization_name=organization.name,
                election_id=None,
                audit_name=None,
                audit_type=None,
                user_type="jurisdiction_admin",
                user_key=user_1.email,
                support_user_email=None,
            ),
            error=None,
        )
    )
    record_login(user_2)

    rv = client.get(f"/api/election/{election_id}/jurisdictions/last-login")
    logins = json.loads(rv.data)
    expectation = {}
    expectation[election.jurisdictions[0].id] = {
        "activityName": "JurisdictionAdminLogin",
        "election": None,
        "id": assert_is_id,
        "info": {"error": None},
        "timestamp": assert_is_date,
        "user": {
            "key": "a2@example.com",
            "supportUser": None,
            "type": "jurisdiction_admin",
        },
    }
    compare_json(logins, {"lastLoginByJurisdiction": expectation})
