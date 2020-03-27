import configparser
import os
import sys

from typing import Dict, Tuple

###
###

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


DEFAULT_DATABASE_URL = "postgres://postgres@localhost:5432/arlo"


def read_database_url_config() -> str:
    environment_database_url = os.environ.get("DATABASE_URL", None)

    if environment_database_url:
        return environment_database_url

    database_cfg_path = os.path.normpath(os.path.join(__file__, "..", "database.cfg"))
    database_config = configparser.ConfigParser()
    database_config.read(database_cfg_path)

    result = database_config.get(FLASK_ENV, "database_url", fallback=None)

    if not result:
        print(
            f"WARNING: no database url was configured, falling back to default: {DEFAULT_DATABASE_URL}",
            file=sys.stderr,
        )
        print(
            f"To configure your own database url, either run with a DATABASE_URL environment variable",
            file=sys.stderr,
        )
        print(
            f"or copy `config/database.cfg.example` to `config/database.cfg` and edit it as needed.",
            file=sys.stderr,
        )

    return result or DEFAULT_DATABASE_URL


DATABASE_URL = read_database_url_config()

STATIC_FOLDER = (
    os.path.normpath(
        os.path.join(
            __file__,
            "..",
            "..",
            "arlo-client",
            "public" if FLASK_ENV == "test" else "build",
        )
    )
    + "/"
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


def read_http_origin() -> str:
    http_origin = os.environ.get("ARLO_HTTP_ORIGIN", None)

    if not http_origin:
        if FLASK_ENV in DEVELOPMENT_ENVS:
            http_origin = "http://localhost:3000"
        elif FLASK_ENV == "staging" and "HEROKU_PR_NUMBER" in os.environ:
            http_origin = f"https://vx-arlo-staging-pr-{os.environ.get('HEROKU_PR_NUMBER')}.herokuapp.com"
        else:
            raise Exception(
                "ARLO_HTTP_ORIGIN env var, e.g. https://arlo.example.com, is missing"
            )

    return http_origin


HTTP_ORIGIN = read_http_origin()


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
