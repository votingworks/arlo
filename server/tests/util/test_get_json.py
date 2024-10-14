from unittest.mock import MagicMock
import pytest
from werkzeug.exceptions import BadRequest
from ...util.get_json import safe_get_json_dict, safe_get_json_list


def test_safe_get_json_dict():
    request = MagicMock()

    request.get_json.return_value = {"key": "value"}
    assert safe_get_json_dict(request) == {"key": "value"}

    with pytest.raises(BadRequest, match="Request content type must be JSON"):
        request.get_json.return_value = None
        safe_get_json_dict(request)

    with pytest.raises(BadRequest, match="Request content must be a JSON object"):
        request.get_json.return_value = []
        safe_get_json_dict(request)


def test_safe_get_json_list():
    request = MagicMock()

    request.get_json.return_value = [{"key": "value"}]
    assert safe_get_json_list(request) == [{"key": "value"}]

    with pytest.raises(BadRequest, match="Request content type must be JSON"):
        request.get_json.return_value = None
        safe_get_json_list(request)

    with pytest.raises(BadRequest, match="Request content must be a JSON array"):
        request.get_json.return_value = {}
        safe_get_json_list(request)
