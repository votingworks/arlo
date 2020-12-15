from urllib.parse import urlparse
import json, pytest
from flask.testing import FlaskClient

from ...auth import UserType
from ...models import *  # pylint: disable=wildcard-import
from ..helpers import *  # pylint: disable=wildcard-import

SA_EMAIL = "superadmin@example.com"


@pytest.fixture()
def organization_id() -> str:
    org_id, _ = create_org_and_admin(user_email=DEFAULT_AA_EMAIL)
    return org_id


@pytest.fixture()
def election_id(client: FlaskClient, organization_id) -> str:
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    election_id = create_election(client, organization_id=organization_id,)
    return election_id


def assert_superadmin_access(client: FlaskClient, url):
    clear_superadmin_user(client)
    rv = client.get(url)
    assert rv.status_code == 403

    set_superadmin_user(client, SA_EMAIL)
    rv = client.get(url)
    assert rv.status_code == 200

    return str(rv.data)


def test_superadmin_organizations(client: FlaskClient, organization_id):
    org = Organization.query.filter_by(id=organization_id).one()
    data = assert_superadmin_access(client, "/superadmin/")
    assert "Organizations" in data
    assert org.name in data
    assert DEFAULT_AA_EMAIL in data

    rv = client.post("/superadmin/auditadmin-login", data={"email": DEFAULT_AA_EMAIL})
    assert rv.status_code == 302

    rv = client.get("/api/me")
    auth_data = json.loads(rv.data)
    assert auth_data["user"]["email"] == DEFAULT_AA_EMAIL
    assert auth_data["user"]["type"] == UserType.AUDIT_ADMIN
    assert auth_data["superadminUser"] == {"email": SA_EMAIL}


def test_superadmin_jurisdictions(client: FlaskClient, election_id):
    create_jurisdiction_and_admin(
        election_id, "Test Jurisdiction", default_ja_email(election_id),
    )

    data = assert_superadmin_access(
        client, f"/superadmin/jurisdictions?election_id={election_id}"
    )

    assert "Jurisdictions" in data
    assert default_ja_email(election_id) in data

    rv = client.post(
        "/superadmin/jurisdictionadmin-login",
        data={"email": default_ja_email(election_id)},
    )
    assert rv.status_code == 302

    rv = client.get("/api/me")
    auth_data = json.loads(rv.data)
    assert auth_data["user"]["email"] == default_ja_email(election_id)
    assert auth_data["user"]["type"] == UserType.JURISDICTION_ADMIN
    assert auth_data["superadminUser"] == {"email": SA_EMAIL}


def test_superadmin_delete_election(
    client: FlaskClient,
    organization_id: str,
    election_id: str,
    round_1_id: str,  # pylint: disable=unused-argument
):
    election_id_2 = create_election(
        client, audit_name="Audit 2", organization_id=organization_id
    )

    set_superadmin_user(client, SA_EMAIL)
    rv = client.post(f"/superadmin/delete-election/{election_id}")
    assert rv.status_code == 302
    assert urlparse(rv.headers["location"]).path == "/superadmin/"

    assert Election.query.get(election_id) is None
    assert Election.query.get(election_id_2) is not None

    # TODO this doesn't work anymore because we no longer provide an empty
    # database to each test. Once we have permission-scoped database queries
    # implemented, we can use them here to check this assertion.
    # for model in [
    #     AuditBoard,
    #     BallotInterpretation,
    #     Batch,
    #     Contest,
    #     ContestChoice,
    #     Jurisdiction,
    #     Round,
    #     RoundContest,
    #     RoundContestResult,
    #     SampledBallot,
    #     SampledBallotDraw,
    # ]:
    #     assert model.query.count() == 0
