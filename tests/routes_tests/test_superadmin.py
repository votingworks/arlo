from flask.testing import FlaskClient
from ..helpers import (
    set_superadmin,
    clear_superadmin,
)


def test_superadmin_organizations(client: FlaskClient):
    url = "/superadmin/"

    clear_superadmin(client)
    rv = client.get(url)
    assert rv.status_code == 403

    set_superadmin(client)
    rv = client.get(url)
    assert rv.status_code == 200
    assert "Organizations" in str(rv.data)
