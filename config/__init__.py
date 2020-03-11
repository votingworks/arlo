import configparser
import os
import sys

from typing import Tuple

DEFAULT_DATABASE_URL = "postgres://postgres@localhost:5432/arlo"


def read_database_url_config() -> str:
    environment_database_url = os.environ.get("DATABASE_URL", None)

    if environment_database_url:
        return environment_database_url

    database_cfg_path = os.path.normpath(os.path.join(__file__, "..", "database.cfg"))
    database_config = configparser.ConfigParser()
    database_config.read(database_cfg_path)

    flask_env = os.environ.get("FLASK_ENV", "development")
    result = database_config.get(flask_env, "database_url", fallback=None)

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
            "public" if os.environ.get("FLASK_ENV") == "test" else "build",
        )
    )
    + "/"
)


def read_session_secret() -> str:
    session_secret = os.environ.get("ARLO_SESSION_SECRET", None)

    if not session_secret:
        flask_env = os.environ.get("FLASK_ENV", "development")

        if flask_env == "development" or flask_env == "test":
            # Allow omitting in development, use a fixed secret instead.
            session_secret = f"arlo-{flask_env}-session-secret-v1"
        else:
            raise Exception(
                "ARLO_SESSION_SECRET env var for managing sessions is missing"
            )

    return session_secret


SESSION_SECRET = read_session_secret()


def read_http_origin() -> str:
    http_origin = os.environ.get("ARLO_HTTP_ORIGIN", None)

    if not http_origin:
        flask_env = os.environ.get("FLASK_ENV", "development")

        if flask_env == "development" or flask_env == "test":
            http_origin = "http://localhost:3000"
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
