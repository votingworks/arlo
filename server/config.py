import os
import logging
from datetime import timedelta
from typing import Dict


def read_env_var(
    name: str, default: str = None, env_defaults: Dict[str, str] = None,
) -> str:
    value = os.environ.get(name, (env_defaults or {}).get(FLASK_ENV, default))
    if value is None:
        raise Exception(f"Missing env var: {name}")
    return value


def parse_bool(value: str) -> bool:
    if value.lower() in ["true", "yes", "1"]:
        return True
    elif value.lower() in ["false", "no", "0"]:
        return False
    else:
        raise Exception(f"Invalid boolean value: {value}")


# Configure Flask-specific environment variables.
# We do this here because Flask attempts to set some of its application config
# based on `FLASK_ENV` and `FLASK_DEBUG` environment variables, and that
# happens _after_ initialization and initial configuration, when calling
# `app.run(…)`. Therefore, we set them here to ensure they end up with the
# right values.
# Specifically, setting FLASK_ENV=test by itself means `app.debug` will remain
# `False`, which isn't what we want.
FLASK_ENV = os.environ.get("FLASK_ENV", "production")
FLASK_DEBUG = read_env_var(
    "FLASK_DEBUG", default="False", env_defaults=dict(development="True", test="True")
)
if "FLASK_DEBUG" not in os.environ:
    os.environ["FLASK_DEBUG"] = str(parse_bool(FLASK_DEBUG))


DATABASE_URL = read_env_var(
    "DATABASE_URL",
    env_defaults=dict(
        development="postgresql://arlo:arlo@localhost:5432/arlo",
        test="postgresql://arlo:arlo@localhost:5432/arlotest",
    ),
)

STATIC_FOLDER = os.path.normpath(
    os.path.join(
        __file__, "..", "..", "client", "public" if FLASK_ENV == "test" else "build",
    )
)

SESSION_SECRET = read_env_var(
    "ARLO_SESSION_SECRET",
    env_defaults=dict(
        development="arlo-dev-session-secret", test="arlo-test-session-secret"
    ),
)

# Max time a session can be used after it's created
SESSION_LIFETIME = timedelta(hours=8)
# Max time a session can be used after the last request
SESSION_INACTIVITY_TIMEOUT = timedelta(hours=1)


HTTP_ORIGIN = read_env_var(
    "ARLO_HTTP_ORIGIN",
    env_defaults=dict(
        development="http://localhost:3000",
        test="http://localhost:3000",
        # For Heroku Review Apps, we need to create the http origin based on the app name.
        staging=f"https://{os.environ.get('HEROKU_APP_NAME')}.herokuapp.com",
    ),
)

# Support user login config
SUPPORT_AUTH0_BASE_URL = read_env_var(
    "ARLO_SUPPORT_AUTH0_BASE_URL", env_defaults=dict(test="")
)
SUPPORT_AUTH0_CLIENT_ID = read_env_var(
    "ARLO_SUPPORT_AUTH0_CLIENT_ID", env_defaults=dict(test="")
)
SUPPORT_AUTH0_CLIENT_SECRET = read_env_var(
    "ARLO_SUPPORT_AUTH0_CLIENT_SECRET", env_defaults=dict(test="")
)
# Required email domain(s) for support users (comma-separated string)
SUPPORT_EMAIL_DOMAINS = read_env_var(
    "ARLO_SUPPORT_EMAIL_DOMAIN", default="voting.works"
).split(",")

# Audit admin OAuth login config
AUDITADMIN_AUTH0_BASE_URL = read_env_var(
    "ARLO_AUDITADMIN_AUTH0_BASE_URL", env_defaults=dict(test="")
)
AUDITADMIN_AUTH0_CLIENT_ID = read_env_var(
    "ARLO_AUDITADMIN_AUTH0_CLIENT_ID", env_defaults=dict(test="")
)
AUDITADMIN_AUTH0_CLIENT_SECRET = read_env_var(
    "ARLO_AUDITADMIN_AUTH0_CLIENT_SECRET", env_defaults=dict(test="")
)

# Jurisdiction admin login code email config
SMTP_HOST = read_env_var("ARLO_SMTP_HOST", env_defaults=dict(test="test-smtp-host"))
SMTP_PORT = int(
    read_env_var("ARLO_SMTP_PORT", env_defaults=dict(development="587", test="587"))
)
SMTP_USERNAME = read_env_var(
    "ARLO_SMTP_USERNAME", env_defaults=dict(test="test-smtp-username")
)
SMTP_PASSWORD = read_env_var(
    "ARLO_SMTP_PASSWORD", env_defaults=dict(test="test-smtp-password")
)
LOGIN_CODE_LIFETIME = timedelta(minutes=15)


# Configure round size growth from ARLO_MINERVA_MULTIPLE (a float) if given, otherwise 1.5
MINERVA_MULTIPLE = float(read_env_var("ARLO_MINERVA_MULTIPLE", default="1.5"))

SENTRY_DSN = os.environ.get("SENTRY_DSN")

SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")

RUN_BACKGROUND_TASKS_IMMEDIATELY = parse_bool(
    read_env_var("RUN_BACKGROUND_TASKS_IMMEDIATELY", default="False")
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("arlo.config")

logger.info(f"{DATABASE_URL=}")
logger.info(f"{HTTP_ORIGIN=}")
logger.info(f"{FLASK_ENV=}")

# Filter out any logging messages from athena/audit.py, in preference to our tighter logging
logging.getLogger().addFilter(
    lambda record: not record.pathname.endswith("athena/audit.py")
)
