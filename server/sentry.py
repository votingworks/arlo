import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from .config import FLASK_ENV, SENTRY_DSN


def configure_sentry():
    sentry_sdk.init(
        SENTRY_DSN,
        environment=FLASK_ENV,
        integrations=[FlaskIntegration()],
        traces_sample_rate=0.2,
    )
