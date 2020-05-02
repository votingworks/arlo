from flask.testing import FlaskClient
from ..helpers import clear_superadmin


def test_superadmin_loadtesting_header_access(client: FlaskClient):
    clear_superadmin(client)
    rv = client.get(
        "/superadmin/",
        headers={"x-arlo-loadtesting-superadmin": "myvoiceismypassportverifyme"},
    )
    assert rv.status_code == 200
