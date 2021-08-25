import json
from flask.testing import FlaskClient

from ..app import app
from .helpers import *  # pylint: disable=wildcard-import


def test_uncaught_exception_500(client: FlaskClient):
    # Need to turn this off to hit the error handler (it's turned on
    # automatically in test)
    app.config["PROPAGATE_EXCEPTIONS"] = False

    rv = client.get("/test_uncaught_exception")
    assert rv.status_code == 500
    assert json.loads(rv.data) == {
        "errors": [
            {"errorType": "Internal Server Error", "message": "Catch me if you can!"}
        ]
    }


def test_internal_error_500(client: FlaskClient):
    app.config["PROPAGATE_EXCEPTIONS"] = False

    rv = client.get("/test_internal_error")
    assert rv.status_code == 500
    assert (
        rv.data
        == b'<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">\n<title>500 Internal Server Error</title>\n<h1>Internal Server Error</h1>\n<p>The server encountered an internal error and was unable to complete your request. Either the server is overloaded or there is an error in the application.</p>\n'
    )
