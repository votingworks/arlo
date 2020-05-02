from flask.testing import FlaskClient
from typing import Generator
import pytest, json

from arlo_server.auth import UserType
from ..helpers import (
    set_superadmin,
    clear_superadmin,
    create_org_and_admin,
    create_jurisdiction_and_admin,
    create_election,
    set_logged_in_user,
    clear_logged_in_user,
)

from arlo_server.models import Organization


SA_TEST_AA_EMAIL = "sa-test-aa-email@example.com"
SA_TEST_JA_EMAIL = "sa-test-ja-email@example.com"


@pytest.fixture()
def organization_id() -> Generator[str, None, None]:
    org_id, audit_admin_id = create_org_and_admin(user_email=SA_TEST_AA_EMAIL)
    yield org_id


@pytest.fixture()
def election_id(client: FlaskClient, organization_id) -> Generator[str, None, None]:
    set_logged_in_user(client, UserType.AUDIT_ADMIN, SA_TEST_AA_EMAIL)
    election_id = create_election(
        client, organization_id=organization_id, is_multi_jurisdiction=True
    )
    clear_logged_in_user(client)
    yield election_id


def assert_superadmin_access(client: FlaskClient, url):
    clear_superadmin(client)
    rv = client.get(url)
    assert rv.status_code == 403

    set_superadmin(client)
    rv = client.get(url)
    assert rv.status_code == 200

    return str(rv.data)


def test_superadmin_organizations(client: FlaskClient, organization_id):
    org = Organization.query.filter_by(id=organization_id).one()
    data = assert_superadmin_access(client, "/superadmin/")
    assert "Organizations" in data
    assert org.name in data
    assert SA_TEST_AA_EMAIL in data

    rv = client.post("/superadmin/auditadmin-login", data={"email": SA_TEST_AA_EMAIL})
    assert rv.status_code == 302

    rv = client.get("/auth/me")
    auth_data = json.loads(rv.data)
    assert auth_data["email"] == SA_TEST_AA_EMAIL
    assert auth_data["type"] == UserType.AUDIT_ADMIN


def test_superadmin_jurisdictions(client: FlaskClient, election_id):
    jurisdiction_id, ja_id = create_jurisdiction_and_admin(
        election_id=election_id, user_email=SA_TEST_JA_EMAIL
    )

    data = assert_superadmin_access(
        client, f"/superadmin/jurisdictions?election_id={election_id}"
    )

    assert "Jurisdictions" in data
    assert SA_TEST_JA_EMAIL in data

    rv = client.post(
        "/superadmin/jurisdictionadmin-login", data={"email": SA_TEST_JA_EMAIL}
    )
    assert rv.status_code == 302

    rv = client.get("/auth/me")
    auth_data = json.loads(rv.data)
    assert auth_data["email"] == SA_TEST_JA_EMAIL
    assert auth_data["type"] == UserType.JURISDICTION_ADMIN
