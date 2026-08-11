from flask import jsonify
from jsonschema.exceptions import ValidationError
from werkzeug.exceptions import (
    Conflict,
    BadRequest,
    Unauthorized,
    InternalServerError,
    Forbidden,
    RequestEntityTooLarge,
)

from .app import app


@app.errorhandler(ValidationError)
def handle_validation_error(error):
    return (
        jsonify(errors=[{"message": error.message, "errorType": "Bad Request"}]),
        BadRequest.code,
    )


@app.errorhandler(BadRequest)
def handle_400(error):
    return (
        jsonify(errors=[{"message": error.description, "errorType": "Bad Request"}]),
        BadRequest.code,
    )


@app.errorhandler(Unauthorized)
def handle_401(error):
    return (
        jsonify(errors=[{"message": error.description, "errorType": "Unauthorized"}]),
        Unauthorized.code,
    )


@app.errorhandler(Conflict)
def handle_409(error):
    return (
        jsonify(errors=[{"message": error.description, "errorType": "Conflict"}]),
        Conflict.code,
    )


@app.errorhandler(Forbidden)
def handle_403(error):
    return (
        jsonify(errors=[{"message": error.description, "errorType": "Forbidden"}]),
        Forbidden.code,
    )


@app.errorhandler(RequestEntityTooLarge)
def handle_413(error):
    max_size_gb = round(app.config["MAX_CONTENT_LENGTH"] / 1024**3, 2)
    return (
        jsonify(
            errors=[
                {
                    "message": f"Upload cannot be larger than {max_size_gb:g} GB",
                    "errorType": "Request Entity Too Large",
                }
            ]
        ),
        RequestEntityTooLarge.code,
    )


@app.errorhandler(InternalServerError)
def handle_500(error):
    original = getattr(error, "original_exception", None)

    if original is None:
        # direct 500 error, such as abort(500)
        return error

    # wrapped unhandled error
    return (
        jsonify(
            errors=[{"message": str(original), "errorType": "Internal Server Error"}]
        ),
        InternalServerError.code,
    )
