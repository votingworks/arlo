from flask import jsonify

from arlo_server import app

# from arlo_server.models import (
#    db,
#    Election,
#    Jurisdiction,
# )
from arlo_server.auth import with_superadmin_access


@app.route(
    "/superadmin", methods=["GET"],
)
@with_superadmin_access
def superadmin_audits():
    return jsonify(status="ok")
