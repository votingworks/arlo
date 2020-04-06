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
from sqlalchemy.exc import IntegrityError

from arlo_server import app


def handle_unique_constraint_error(
    e: IntegrityError, constraint_name: str, message: str
):
    if e.orig.diag.constraint_name == constraint_name:
        raise Conflict(message)
    else:
        raise e


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
        jsonify(errors=[{"message": e.description, "errorType": type(e).__name__}]),
        Unauthorized.code,
    )


@app.errorhandler(Conflict)
def handle_409(e):
    return (
        jsonify(errors=[{"message": e.description, "errorType": type(e).__name__}]),
        Conflict.code,
    )


@app.errorhandler(Forbidden)
def handle_403(e):
    return (
        jsonify(errors=[{"message": e.description, "errorType": type(e).__name__}]),
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
            errors=[{"message": str(original), "errorType": type(original).__name__}]
        ),
        InternalServerError.code,
    )
