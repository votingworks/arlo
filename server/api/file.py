from flask import jsonify, request
from werkzeug.exceptions import BadRequest

from . import api
from ..auth import restrict_access, UserType
from ..models import *  # pylint: disable=wildcard-import

from ..util.file import (
    store_file,
)


@api.route(
    "/file-upload",
    methods=["POST"],
)
@restrict_access([UserType.AUDIT_ADMIN, UserType.JURISDICTION_ADMIN])
def upload_file_to_local_filesystem(
    election: Election,  # pylint: disable=unused-argument
    jurisdiction: Jurisdiction,  # pylint: disable=unused-argument
):
    file = request.files["file"]
    storage_key = request.form.get("key")
    if storage_key is None:
        raise BadRequest("Missing required form parameter 'key'")
    if file is None:
        raise BadRequest("Missing required form parameter 'file'")

    store_file(
        file.stream,
        storage_key,
    )
    return jsonify(status="ok")
