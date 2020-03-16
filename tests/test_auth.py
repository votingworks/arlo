import pytest, json, uuid
from unittest.mock import patch, Mock, MagicMock

from arlo_server import app
from arlo_server.routes import (
    set_loggedin_user,
    clear_loggedin_user,
    auth0_aa,
    auth0_ja,
    create_organization,
    create_election,
    UserType,
)
from arlo_server.models import *
from tests.helpers import create_org_and_admin


@pytest.fixture
def client():
    app.config["TESTING"] = True
    client = app.test_client()

    yield client


def _setup_user(client, user_type, user_email):
    with client.session_transaction() as session:
        session["_user"] = {"type": user_type, "email": user_email}


def test_auth_me(client):
    org_id, user_id = create_org_and_admin("Test Org", "admin@example.com")
    election_id = create_election(organization_id=org_id)
    jurisdiction = Jurisdiction(
        election_id=election_id, id=str(uuid.uuid4()), name="Test Jurisdiction"
    )
    j_admin = JurisdictionAdministration(
        user_id=user_id, jurisdiction_id=jurisdiction.id
    )
    j_id = jurisdiction.id

    db.session.add(jurisdiction)
    db.session.add(j_admin)
    db.session.commit()

    _setup_user(client, UserType.AUDIT_ADMIN, "admin@example.com")

    rv = client.get("/auth/me")
    assert json.loads(rv.data) == {
        "type": UserType.AUDIT_ADMIN,
        "email": "admin@example.com",
        "organizations": [
            {
                "name": "Test Org",
                "id": org_id,
                "elections": [
                    {
                        "id": election_id,
                        "name": "",
                        "state": None,
                        "election_date": None,
                    }
                ],
            }
        ],
        "jurisdictions": [
            {
                "id": j_id,
                "name": "Test Jurisdiction",
                "election": {
                    "id": election_id,
                    "name": "",
                    "state": None,
                    "election_date": None,
                },
            }
        ],
    }


def test_auditadmin_start(client):
    rv = client.get("/auth/auditadmin/start")
    assert rv.status_code == 302


def test_auditadmin_callback(client):
    create_org_and_admin("Test Organization", "foo@example.com")

    auth0_aa.authorize_access_token = MagicMock(return_value=None)

    mock_response = Mock()
    mock_response.json = MagicMock(return_value={"email": "foo@example.com"})
    auth0_aa.get = Mock(return_value=mock_response)

    rv = client.get("/auth/auditadmin/callback?code=foobar")
    assert rv.status_code == 302

    with client.session_transaction() as session:
        assert session["_user"]["type"] == UserType.AUDIT_ADMIN
        assert session["_user"]["email"] == "foo@example.com"

    assert auth0_aa.authorize_access_token.called
    assert auth0_aa.get.called


def test_jurisdictionadmin_start(client):
    rv = client.get("/auth/jurisdictionadmin/start")
    assert rv.status_code == 302


def test_jurisdictionadmin_callback(client):
    org = create_organization("Test Organization")
    election_id = create_election(organization_id=org.id)
    jurisdiction = Jurisdiction(
        election_id=election_id, id=str(uuid.uuid4()), name="Test Jurisdiction"
    )
    u = User(
        id=str(uuid.uuid4()), email="bar@example.com", external_id="bar@example.com"
    )
    j_admin = JurisdictionAdministration(user_id=u.id, jurisdiction_id=jurisdiction.id)

    db.session.add(jurisdiction)
    db.session.add(u)
    db.session.add(j_admin)
    db.session.commit()

    auth0_ja.authorize_access_token = MagicMock(return_value=None)

    mock_response = Mock()
    mock_response.json = MagicMock(return_value={"email": "bar@example.com"})
    auth0_ja.get = Mock(return_value=mock_response)

    rv = client.get("/auth/jurisdictionadmin/callback?code=foobar")
    assert rv.status_code == 302

    with client.session_transaction() as session:
        assert session["_user"]["type"] == UserType.JURISDICTION_ADMIN
        assert session["_user"]["email"] == "bar@example.com"

    assert auth0_ja.authorize_access_token.called
    assert auth0_ja.get.called


def test_logout(client):
    _setup_user(client, UserType.AUDIT_ADMIN, "admin@example.com")

    rv = client.get("/auth/logout")

    with client.session_transaction() as session:
        assert session["_user"] is None

    assert rv.status_code == 302
