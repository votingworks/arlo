import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from flask import Flask, session, request
from .models import Election
from .config import FLASK_ENV, SENTRY_DSN
from .auth.lib import get_loggedin_user


def set_sentry_user():
    user_type, user_key = get_loggedin_user(session)
    sentry_sdk.set_user(dict(username=user_key, user_type=user_type))

    election_id = request.view_args.get("election_id")
    if election_id:
        sentry_sdk.set_tag("election_id", election_id)
        election = Election.query.get(election_id)
        sentry_sdk.set_tag("audit_name", election and election.audit_name)
        sentry_sdk.set_tag("organization_name", election and election.organization.name)


def configure_sentry(app: Flask = None):
    sentry_sdk.init(
        SENTRY_DSN,
        environment=FLASK_ENV,
        integrations=[FlaskIntegration()],
        traces_sample_rate=0.2,
    )

    if app:
        app.before_request(set_sentry_user)
