from flask import jsonify
from jsonschema.exceptions import ValidationError
from werkzeug.exceptions import (
    Conflict,
    BadRequest,
    Unauthorized,
    Conflict,
    InternalServerError,
    Forbidden,
)

from arlo_server import app


@app.errorhandler(ValidationError)
def handle_validation_error(e):
    return (
        jsonify(errors=[{"message": e.message, "errorType": "Bad Request"}]),
        BadRequest.code,
    )


@app.errorhandler(BadRequest)
def handle_400(e):
    return (
        jsonify(errors=[{"message": e.description, "errorType": "Bad Request"}]),
        BadRequest.code,
    )


@app.errorhandler(Unauthorized)
def handle_401(e):
    return (
        jsonify(errors=[{"message": e.description, "errorType": "Unauthorized"}]),
        Unauthorized.code,
    )


@app.errorhandler(Conflict)
def handle_409(e):
    return (
        jsonify(errors=[{"message": e.description, "errorType": "Conflict"}]),
        Conflict.code,
    )


@app.errorhandler(Forbidden)
def handle_403(e):
    return (
        jsonify(errors=[{"message": e.description, "errorType": "Forbidden"}]),
        Forbidden.code,
    )


@app.errorhandler(InternalServerError)
def handle_500(e):
    original = getattr(e, "original_exception", None)

    if original is None:
        # direct 500 error, such as abort(500)
        return e

    # wrapped unhandled error
    return (
        jsonify(
            errors=[{"message": str(original), "errorType": "Internal Server Error"}]
        ),
        InternalServerError.code,
    )
