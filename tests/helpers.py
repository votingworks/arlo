import uuid
import json
from arlo_server import create_organization, db, UserType
from models import AuditAdministration, User  # type: ignore
from typing import Any, Optional
from flask.testing import FlaskClient

DEFAULT_USER_EMAIL = "admin@example.com"


def post_json(client: FlaskClient, url: str, obj) -> Any:
    return client.post(
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
