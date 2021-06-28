from unittest.mock import Mock, patch
from urllib.parse import urlparse
from flask.testing import FlaskClient

from ..helpers import *  # pylint: disable=wildcard-import
from ...api.support import (
    AUTH0_DOMAIN,
    AUDITADMIN_AUTH0_CLIENT_ID,
    AUDITADMIN_AUTH0_CLIENT_SECRET,
    Auth0Error,
)

SUPPORT_EMAIL = "support@example.org"


def test_support_list_organizations(client: FlaskClient, org_id: str):
    set_support_user(client, SUPPORT_EMAIL)
    rv = client.get("/api/support/organizations")
    orgs = json.loads(rv.data)
    # This will load orgs from all tests, so we can't check its exact length/value
    assert len(orgs) >= 1
    org = next(org for org in orgs if org["id"] == org_id)
    assert org == {"id": org_id, "name": "Test Org test_support_list_organizations"}


def test_support_create_organization(client: FlaskClient):
    set_support_user(client, SUPPORT_EMAIL)
    rv = post_json(client, "/api/support/organizations", {"name": "New Organization"})
    assert_ok(rv)

    rv = client.get("/api/support/organizations")
    orgs = json.loads(rv.data)
    org = next(org for org in orgs if org["name"] == "New Organization")
    assert_is_id(org["id"])

    # Can't create another org with the same name
    rv = post_json(client, "/api/support/organizations", {"name": "New Organization"})
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [{"errorType": "Conflict", "message": "Organization already exists"}]
    }


def test_support_get_organization(client: FlaskClient, org_id: str, election_id: str):
    set_support_user(client, SUPPORT_EMAIL)
    rv = client.get(f"/api/support/organizations/{org_id}")
    compare_json(
        json.loads(rv.data),
        {
            "id": org_id,
            "name": "Test Org test_support_get_organization",
            "elections": [
                {
                    "id": election_id,
                    "auditName": "Test Audit test_support_get_organization",
                    "auditType": "BALLOT_POLLING",
                    "online": False,
                }
            ],
            "auditAdmins": [{"email": DEFAULT_AA_EMAIL}],
        },
    )


def test_support_get_election(
    client: FlaskClient, election_id: str, jurisdiction_ids: List[str]
):
    set_support_user(client, SUPPORT_EMAIL)
    rv = client.get(f"/api/support/elections/{election_id}")
    compare_json(
        json.loads(rv.data),
        {
            "id": election_id,
            "auditName": "Test Audit test_support_get_election",
            "auditType": "BALLOT_POLLING",
            "online": False,
            "jurisdictions": [
                {"id": jurisdiction_ids[0], "name": "J1",},
                {"id": jurisdiction_ids[1], "name": "J2",},
                {"id": jurisdiction_ids[2], "name": "J3",},
            ],
        },
    )


@patch("server.api.support.GetToken")
@patch("server.api.support.Auth0")
def test_support_create_audit_admin(  # pylint: disable=invalid-name
    MockAuth0, MockGetToken, client: FlaskClient, org_id: str,
):
    MockGetToken.return_value = Mock()
    MockGetToken.return_value.client_credentials = Mock(
        return_value={"access_token": "test token"}
    )
    MockAuth0.return_value = Mock()
    MockAuth0.return_value.users = Mock()
    MockAuth0.return_value.users.create = Mock(
        return_value={"user_id": "test auth0 user id"}
    )

    new_admin_email = f"new-audit-admin-{org_id}@example.com"

    set_support_user(client, SUPPORT_EMAIL)
    rv = post_json(
        client,
        f"/api/support/organizations/{org_id}/audit-admins",
        {"email": new_admin_email},
    )
    assert_ok(rv)

    rv = client.get(f"/api/support/organizations/{org_id}")
    assert json.loads(rv.data)["auditAdmins"] == [
        {"email": DEFAULT_AA_EMAIL},
        {"email": new_admin_email},
    ]

    user = User.query.filter_by(email=new_admin_email).one()
    assert user.external_id == "test auth0 user id"

    MockGetToken.assert_called_with(AUTH0_DOMAIN)
    MockGetToken.return_value.client_credentials.assert_called_with(
        AUDITADMIN_AUTH0_CLIENT_ID,
        AUDITADMIN_AUTH0_CLIENT_SECRET,
        f"https://{AUTH0_DOMAIN}/api/v2/",
    )
    MockAuth0.assert_called_with(AUTH0_DOMAIN, "test token")
    MockAuth0.return_value.users.create.assert_called()
    create_spec = MockAuth0.return_value.users.create.call_args[0][0]
    assert create_spec["email"] == f"new-audit-admin-{org_id}@example.com"
    assert create_spec["password"]
    assert create_spec["connection"] == "Username-Password-Authentication"


@patch("server.api.support.GetToken")
@patch("server.api.support.Auth0")
def test_support_create_audit_admin_already_in_auth0(  # pylint: disable=invalid-name
    MockAuth0, MockGetToken, client: FlaskClient, org_id: str,
):
    MockGetToken.return_value = Mock()
    MockGetToken.return_value.client_credentials = Mock(
        return_value={"access_token": "test token"}
    )
    MockAuth0.return_value = Mock()
    MockAuth0.return_value.users = Mock()
    MockAuth0.return_value.users.create = Mock(
        side_effect=Auth0Error(409, 1, "already exists")
    )
    MockAuth0.return_value.users_by_email = Mock()
    MockAuth0.return_value.users_by_email.search_users_by_email = Mock(
        return_value=[{"user_id": "test auth0 existing user id"}]
    )

    new_admin_email = f"new-audit-admin-{org_id}@example.com"

    set_support_user(client, SUPPORT_EMAIL)
    rv = post_json(
        client,
        f"/api/support/organizations/{org_id}/audit-admins",
        {"email": new_admin_email},
    )
    assert_ok(rv)

    rv = client.get(f"/api/support/organizations/{org_id}")
    assert json.loads(rv.data)["auditAdmins"] == [
        {"email": DEFAULT_AA_EMAIL},
        {"email": new_admin_email},
    ]

    user = User.query.filter_by(email=new_admin_email).one()
    assert user.external_id == "test auth0 existing user id"

    MockAuth0.return_value.users.create.assert_called()
    MockAuth0.return_value.users_by_email.search_users_by_email.assert_called_with(
        new_admin_email
    )


@patch("server.api.support.GetToken")
@patch("server.api.support.Auth0")
def test_support_create_audit_admin_already_exists(  # pylint: disable=invalid-name,unused-argument
    MockAuth0, MockGetToken, client: FlaskClient, org_id: str,
):
    # Start with an existing user that isn't already an audit admin for this org
    user = create_user(email="already-exists@example.org")

    set_support_user(client, SUPPORT_EMAIL)
    rv = client.get(f"/api/support/organizations/{org_id}")
    assert json.loads(rv.data)["auditAdmins"] == [
        {"email": DEFAULT_AA_EMAIL},
    ]

    rv = post_json(
        client,
        f"/api/support/organizations/{org_id}/audit-admins",
        {"email": user.email},
    )
    assert_ok(rv)

    rv = client.get(f"/api/support/organizations/{org_id}")
    assert json.loads(rv.data)["auditAdmins"] == [
        {"email": DEFAULT_AA_EMAIL},
        {"email": user.email},
    ]


@patch("server.api.support.GetToken")
@patch("server.api.support.Auth0")
def test_support_create_audit_admin_already_admin(  # pylint: disable=invalid-name,unused-argument
    MockAuth0, MockGetToken, client: FlaskClient, org_id: str,
):
    set_support_user(client, SUPPORT_EMAIL)
    rv = post_json(
        client,
        f"/api/support/organizations/{org_id}/audit-admins",
        {"email": DEFAULT_AA_EMAIL},
    )
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [{"errorType": "Conflict", "message": "Audit admin already exists"}]
    }


def test_support_get_jurisdiction(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    audit_board_round_1_ids: List[str],
):
    set_support_user(client, SUPPORT_EMAIL)
    rv = client.get(f"/api/support/jurisdictions/{jurisdiction_ids[0]}")
    compare_json(
        json.loads(rv.data),
        {
            "id": jurisdiction_ids[0],
            "name": "J1",
            "election": {
                "id": election_id,
                "auditName": "Test Audit test_support_get_jurisdiction",
                "auditType": "BALLOT_POLLING",
                "online": True,
            },
            "jurisdictionAdmins": [{"email": default_ja_email(election_id)}],
            "auditBoards": [
                {"id": id, "name": f"Audit Board #{i+1}", "signedOffAt": None}
                for i, id in enumerate(audit_board_round_1_ids)
            ],
            "recordedResultsAt": None,
        },
    )


def test_support_log_in_as_audit_admin(
    client: FlaskClient, election_id: str,  # pylint: disable=unused-argument
):
    set_support_user(client, SUPPORT_EMAIL)

    with client.session_transaction() as session:  # type: ignore
        original_created_at = session["_created_at"]
        original_last_request_at = session["_last_request_at"]

    rv = client.get(f"/api/support/audit-admins/{DEFAULT_AA_EMAIL}/login")
    assert rv.status_code == 302
    assert urlparse(rv.location).path == "/"

    with client.session_transaction() as session:  # type: ignore
        assert session["_user"]["type"] == UserType.AUDIT_ADMIN
        assert session["_user"]["key"] == DEFAULT_AA_EMAIL
        assert session["_created_at"] == original_created_at
        assert session["_last_request_at"] != original_last_request_at


def test_support_log_in_as_jurisdiction_admin(
    client: FlaskClient, election_id: str,
):
    set_support_user(client, SUPPORT_EMAIL)

    with client.session_transaction() as session:  # type: ignore
        original_created_at = session["_created_at"]
        original_last_request_at = session["_last_request_at"]

    rv = client.get(
        f"/api/support/jurisdiction-admins/{default_ja_email(election_id)}/login"
    )
    assert rv.status_code == 302
    assert urlparse(rv.location).path == "/"

    with client.session_transaction() as session:  # type: ignore
        assert session["_user"]["type"] == UserType.JURISDICTION_ADMIN
        assert session["_user"]["key"] == default_ja_email(election_id)
        assert session["_created_at"] == original_created_at
        assert session["_last_request_at"] != original_last_request_at


def test_support_clear_audit_boards(
    client: FlaskClient,
    contest_ids: List[str],
    jurisdiction_ids: List[str],
    audit_board_round_1_ids: List[str],
):
    set_support_user(client, SUPPORT_EMAIL)

    # Can't clear if no audit boards
    rv = client.delete(f"/api/support/jurisdictions/{jurisdiction_ids[1]}/audit-boards")
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {"errorType": "Conflict", "message": "Jurisdiction has no audit boards"}
        ]
    }

    # Can't clear if ballots audited
    ballot = AuditBoard.query.get(audit_board_round_1_ids[0]).sampled_ballots[0]
    audit_ballot(ballot, contest_ids[0], Interpretation.BLANK)
    rv = client.delete(f"/api/support/jurisdictions/{jurisdiction_ids[0]}/audit-boards")
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Conflict",
                "message": "Can't clear audit boards after ballots have been audited",
            }
        ]
    }
    db_session.delete(ballot)

    # Happy path
    rv = client.delete(f"/api/support/jurisdictions/{jurisdiction_ids[0]}/audit-boards")
    assert_ok(rv)

    assert Jurisdiction.query.get(jurisdiction_ids[0]).audit_boards == []


def test_support_reopen_audit_board(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: List[str],
    round_1_id: str,
    audit_board_round_1_ids: List[str],
):
    set_support_user(client, SUPPORT_EMAIL)

    # Can't reopen if audit board hasn't signed off
    rv = client.delete(
        f"/api/support/audit-boards/{audit_board_round_1_ids[0]}/sign-off"
    )
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {"errorType": "Conflict", "message": "Audit board has not signed off."}
        ]
    }

    run_audit_round(round_1_id, contest_ids[0], contest_ids, 0.55)

    # Can't reopen after round ends before starting next round
    rv = client.delete(
        f"/api/support/audit-boards/{audit_board_round_1_ids[0]}/sign-off"
    )
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Conflict",
                "message": "Can't reopen audit board after round ends.",
            }
        ]
    }

    # Start round 2
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = post_json(client, f"/api/election/{election_id}/round", {"roundNum": 2},)
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/round",)
    rounds = json.loads(rv.data)["rounds"]
    round_2_id = str(rounds[1]["id"])

    # Can't reopen audit boards from previous rounds
    set_support_user(client, SUPPORT_EMAIL)
    rv = client.delete(
        f"/api/support/audit-boards/{audit_board_round_1_ids[0]}/sign-off"
    )
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Conflict",
                "message": "Audit board is not part of the current round.",
            }
        ]
    }

    # Create audit boards
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_2_id}/audit-board",
        [{"name": "Audit Board #1"}, {"name": "Audit Board #2"},],
    )
    assert_ok(rv)

    # Audit ballots
    audit_board = AuditBoard.query.filter_by(
        jurisdiction_id=jurisdiction_ids[0], round_id=round_2_id
    ).first()
    audit_board.member_1 = "A"
    audit_board.member_2 = "B"
    for ballot in audit_board.sampled_ballots:
        audit_ballot(ballot, contest_ids[0], Interpretation.BLANK)
    db_session.commit()

    set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board.id)
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_2_id}/audit-board/{audit_board.id}/sign-off",
        {"memberName1": audit_board.member_1, "memberName2": audit_board.member_2},
    )
    assert_ok(rv)

    # Happy path
    set_support_user(client, SUPPORT_EMAIL)
    rv = client.delete(f"/api/support/audit-boards/{audit_board.id}/sign-off")
    assert_ok(rv)

    assert AuditBoard.query.get(audit_board.id).signed_off_at is None


# See test_batch_comparison.py for batch comparison test case
def test_support_clear_offline_results_ballot_polling(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: List[str],
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
):
    election = Election.query.get(election_id)
    election.online = False
    db_session.commit()

    set_support_user(client, SUPPORT_EMAIL)
    rv = client.get(f"/api/support/jurisdictions/{jurisdiction_ids[0]}")
    assert json.loads(rv.data)["recordedResultsAt"] is None

    # Can't clear results if audit hasn't started
    rv = client.delete(f"/api/support/jurisdictions/{jurisdiction_ids[0]}/results")
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [{"errorType": "Conflict", "message": "Audit has not started.",}]
    }

    # Start the round
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/sample-sizes")
    sample_sizes = json.loads(rv.data)["sampleSizes"]
    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {
            "roundNum": 1,
            "sampleSizes": {contest_ids[0]: sample_sizes[contest_ids[0]][0]},
        },
    )
    assert_ok(rv)
    rv = client.get(f"/api/election/{election_id}/round")
    round_1_id = json.loads(rv.data)["rounds"][0]["id"]

    # Can't clear results if results haven't been recorded yet
    rv = client.delete(f"/api/support/jurisdictions/{jurisdiction_ids[0]}/results")
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Conflict",
                "message": "Jurisdiction doesn't have any results recorded.",
            }
        ]
    }

    # Create audit boards and record results
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
        [{"name": "Audit Board #1"}],
    )
    assert_ok(rv)
    contests = (
        Contest.query.filter_by(election_id=election_id)
        .order_by(Contest.created_at)
        .all()
    )
    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/results",
        {
            contest.id: {choice.id: 1 for choice in contest.choices}
            for contest in contests
        },
    )
    assert_ok(rv)
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/results"
    )

    rv = client.get(f"/api/support/jurisdictions/{jurisdiction_ids[0]}")
    assert_is_date(json.loads(rv.data)["recordedResultsAt"])

    # Clear results
    rv = client.delete(f"/api/support/jurisdictions/{jurisdiction_ids[0]}/results")
    assert_ok(rv)

    contests = (
        Contest.query.filter_by(election_id=election_id)
        .order_by(Contest.created_at)
        .all()
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/results"
    )
    assert json.loads(rv.data) == {
        contest.id: {choice.id: None for choice in contest.choices}
        for contest in contests
    }

    rv = client.get(f"/api/support/jurisdictions/{jurisdiction_ids[0]}")
    assert json.loads(rv.data)["recordedResultsAt"] is None

    # End the round
    election = Election.query.get(election_id)
    end_round(election, election.rounds[0])

    # Can't clear results after round ends
    rv = client.delete(f"/api/support/jurisdictions/{jurisdiction_ids[0]}/results")
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Conflict",
                "message": "Can't clear results after round ends.",
            }
        ]
    }
