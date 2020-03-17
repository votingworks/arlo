import uuid, json, re
from email.utils import parsedate_to_datetime
from typing import Any, Optional
from flask.testing import FlaskClient

from arlo_server.routes import create_organization, UserType
from arlo_server.models import db, AuditAdministration, User  # type: ignore

DEFAULT_USER_EMAIL = "admin@example.com"


def post_json(client: FlaskClient, url: str, obj) -> Any:
    return client.post(
        url, headers={"Content-Type": "application/json"}, data=json.dumps(obj)
    )


def put_json(client: FlaskClient, url: str, obj) -> Any:
    return client.put(
        url, headers={"Content-Type": "application/json"}, data=json.dumps(obj)
    )


def set_logged_in_user(
    client: FlaskClient, user_type: UserType, user_email=DEFAULT_USER_EMAIL
):
    with client.session_transaction() as session:
        session["_user"] = {"type": user_type, "email": user_email}


def create_user(email=DEFAULT_USER_EMAIL):
    user = User(id=str(uuid.uuid4()), email=email, external_id=email)
    db.session.add(user)
    db.session.commit()
    return user


def create_org_and_admin(org_name="Test Org", user_email=DEFAULT_USER_EMAIL):
    org = create_organization(org_name)
    u = create_user(user_email)
    db.session.add(u)
    admin = AuditAdministration(organization_id=org.id, user_id=u.id)
    db.session.add(admin)
    db.session.commit()

    return org.id, u.id


def assert_is_id(x):
    assert isinstance(x, str)
    uuid.UUID(x, version=4)  # Will raise exception on non-UUID strings


def assert_is_date(x):
    assert isinstance(x, str)
    parsedate_to_datetime(x)  # Will raise exception on non-HTTP-date strings


def assert_is_passphrase(x):
    assert isinstance(x, str)
    assert re.match(r"[a-z]+-[a-z]+-[a-z]+-[a-z]+", x)


# Checks that a json blob (represented as a Python dict) is equal-ish to an expected
# dict. The expected dict can contain assertion functions in place of any non-deterministic values.
def compare_json(actual_json, expected_json):
    if isinstance(expected_json, dict):
        assert isinstance(actual_json, dict)
        for k, v in expected_json.items():
            compare_json(actual_json[k], v)
        assert actual_json.keys() == expected_json.keys()
    elif isinstance(expected_json, list):
        assert isinstance(actual_json, list)
        for i, v in enumerate(expected_json):
            compare_json(actual_json[i], v)
        assert len(actual_json) == len(expected_json)
    elif callable(expected_json):
        expected_json(actual_json)
    else:
        assert (
            actual_json == expected_json
        ), f"Actual: {actual_json}\nExpected: {expected_json}"
