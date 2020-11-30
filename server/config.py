import os
import logging
from typing import Tuple
from datetime import timedelta


DEVELOPMENT_ENVS = ("development", "test")


def setup_flask_config() -> Tuple[str, bool]:
    """
    Configure Flask-specific environment variables.

    We do this here because Flask attempts to set some of its application config
    based on `FLASK_ENV` and `FLASK_DEBUG` environment variables, and that
    happens _after_ initialization and initial configuration, when calling
    `app.run(…)`. Therefore, we set them here to ensure they end up with the
    right values.

    Specifically, setting FLASK_ENV=test by itself means `app.debug` will remain
    `False`, which isn't what we want.
    """
    flask_env = os.environ.get("FLASK_ENV", "production")

    if "FLASK_DEBUG" not in os.environ:
        os.environ["FLASK_DEBUG"] = str(flask_env in DEVELOPMENT_ENVS)

    return (flask_env, os.environ["FLASK_DEBUG"].lower() not in ("0", "no", "false"))


FLASK_ENV, FLASK_DEBUG = setup_flask_config()


def setup_logging():
    "Use $ARLO_LOGLEVEL (an integer) if given, otherwise a default based on FLASK_ENV"

    arlo_loglevel = os.environ.get("ARLO_LOGLEVEL", None)

    if arlo_loglevel is None:
        loglevel = logging.DEBUG if FLASK_ENV == "development" else logging.WARNING
    else:
        loglevel = int(arlo_loglevel)

    return loglevel


LOGLEVEL = setup_logging()
logging.basicConfig(
    format="%(asctime)s:%(name)s:%(levelname)s:%(message)s", level=LOGLEVEL
)
logging.debug("Test debug log")
logging.warning(f"Arlo running at loglevel {LOGLEVEL}")


def filter_athena_messages(record):
    "Filter out any logging messages from athena/audit.py, in preference to our tighter logging"

    return not record.pathname.endswith("athena/audit.py")


logging.getLogger().addFilter(filter_athena_messages)


DEVELOPMENT_DATABASE_URL = "postgresql://arlo:arlo@localhost:5432/arlo"
TEST_DATABASE_URL = "postgresql://arlo:arlo@localhost:5432/arlotest"


def read_database_url_config() -> str:
    environment_database_url = os.environ.get("DATABASE_URL", None)
    logging.warning(f"environment_database_url = {environment_database_url}")
    if environment_database_url:
        return environment_database_url

    if FLASK_ENV == "development":
        return DEVELOPMENT_DATABASE_URL
    elif FLASK_ENV == "test":
        return TEST_DATABASE_URL
    else:
        raise Exception("Missing DATABASE_URL env var")


DATABASE_URL = read_database_url_config()

STATIC_FOLDER = os.path.normpath(
    os.path.join(
        __file__, "..", "..", "client", "public" if FLASK_ENV == "test" else "build",
    )
)


def read_session_secret() -> str:
    session_secret = os.environ.get("ARLO_SESSION_SECRET", None)

    if not session_secret:
        if FLASK_ENV in DEVELOPMENT_ENVS:
            # Allow omitting in development, use a fixed secret instead.
            session_secret = f"arlo-{FLASK_ENV}-session-secret-v1"
        else:
            raise Exception(
                "ARLO_SESSION_SECRET env var for managing sessions is missing"
            )

    return session_secret


SESSION_SECRET = read_session_secret()

# Max time a session can be used after it's created
SESSION_LIFETIME = timedelta(hours=8)
# Max time a session can be used after the last request
SESSION_INACTIVITY_TIMEOUT = timedelta(hours=1)


def read_http_origin() -> str:
    http_origin = os.environ.get("ARLO_HTTP_ORIGIN", None)

    logging.warning(f"ARLO_HTTP_ORIGIN={http_origin}")
    logging.warning(
        f"FLASK_ENV={FLASK_ENV}, HEROKU_APP_NAME={os.environ.get('HEROKU_APP_NAME')}"
    )

    if not http_origin:
        if FLASK_ENV in DEVELOPMENT_ENVS:
            http_origin = "http://localhost:3000"
        # For Heroku Review Apps, which get created automatically for each pull
        # request, we need to create the http origin based on the app name.
        elif FLASK_ENV == "staging":
            http_origin = f"https://{os.environ.get('HEROKU_APP_NAME')}.herokuapp.com"
        else:
            raise Exception(
                "ARLO_HTTP_ORIGIN env var, e.g. https://arlo.example.com, is missing"
            )

    return http_origin


HTTP_ORIGIN = read_http_origin()


def read_superadmin_auth0_creds() -> Tuple[str, str, str, str]:
    return (
        os.environ.get("ARLO_SUPERADMIN_AUTH0_BASE_URL", ""),
        os.environ.get("ARLO_SUPERADMIN_AUTH0_CLIENT_ID", ""),
        os.environ.get("ARLO_SUPERADMIN_AUTH0_CLIENT_SECRET", ""),
        os.environ.get("ARLO_SUPERADMIN_EMAIL_DOMAIN", "voting.works"),
    )


(
    SUPERADMIN_AUTH0_BASE_URL,
    SUPERADMIN_AUTH0_CLIENT_ID,
    SUPERADMIN_AUTH0_CLIENT_SECRET,
    SUPERADMIN_EMAIL_DOMAIN,
) = read_superadmin_auth0_creds()


def read_auditadmin_auth0_creds() -> Tuple[str, str, str]:
    return (
        os.environ.get("ARLO_AUDITADMIN_AUTH0_BASE_URL", ""),
        os.environ.get("ARLO_AUDITADMIN_AUTH0_CLIENT_ID", ""),
        os.environ.get("ARLO_AUDITADMIN_AUTH0_CLIENT_SECRET", ""),
    )


(
    AUDITADMIN_AUTH0_BASE_URL,
    AUDITADMIN_AUTH0_CLIENT_ID,
    AUDITADMIN_AUTH0_CLIENT_SECRET,
) = read_auditadmin_auth0_creds()


def read_jurisdictionadmin_auth0_creds() -> Tuple[str, str, str]:
    return (
        os.environ.get("ARLO_JURISDICTIONADMIN_AUTH0_BASE_URL", ""),
        os.environ.get("ARLO_JURISDICTIONADMIN_AUTH0_CLIENT_ID", ""),
        os.environ.get("ARLO_JURISDICTIONADMIN_AUTH0_CLIENT_SECRET", ""),
    )


(
    JURISDICTIONADMIN_AUTH0_BASE_URL,
    JURISDICTIONADMIN_AUTH0_CLIENT_ID,
    JURISDICTIONADMIN_AUTH0_CLIENT_SECRET,
) = read_jurisdictionadmin_auth0_creds()


def setup_minerva():
    "Configure round size growth from $ARLO_MINERVA_MULTIPLE (a float) if given, otherwise 1.5"

    arlo_minerva_multiple = os.environ.get("ARLO_MINERVA_MULTIPLE", "1.5")

    minerva_multiple = float(arlo_minerva_multiple)
    logging.warning(f"Round sizes will increase by MINERVA_MULTIPLE={minerva_multiple}")

    return minerva_multiple


MINERVA_MULTIPLE = setup_minerva()

SENTRY_DSN = os.environ.get("SENTRY_DSN")
