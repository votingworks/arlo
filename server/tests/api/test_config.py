import json
from flask.testing import FlaskClient

from ..helpers import *  # pylint: disable=wildcard-import
from ... import config


def test_config(client: FlaskClient):
    config.ALLOW_ALTERNATE_MATH = True
    clear_logged_in_user(client)
    rv = client.get("/api/config")
    assert rv.status_code == 200
    assert json.loads(rv.data)["allowAlternateMath"]
