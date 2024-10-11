from typing import List
import typing
from flask import Request
from werkzeug.exceptions import BadRequest
from .jsonschema import JSONDict


def safe_get_json_dict(request: Request) -> JSONDict:
    maybe_json = request.get_json()
    if maybe_json is None:
        raise BadRequest("Request content type must be JSON")
    if not isinstance(maybe_json, dict):
        raise BadRequest("Request content must be a JSON object")
    return typing.cast(JSONDict, maybe_json)


def safe_get_json_list(request: Request) -> List[JSONDict]:
    maybe_json = request.get_json()
    if maybe_json is None:
        raise BadRequest("Request content type must be JSON")
    if not isinstance(maybe_json, list):
        raise BadRequest("Request content must be a JSON array")
    return typing.cast(List[JSONDict], maybe_json)
