import pytest
from jsonschema.exceptions import ValidationError
from ...util.jsonschema import validate_schema

VALID_SCHEMAS = [
    {"type": "string"},
    {"type": "boolean"},
    {"type": "array", "items": {"type": "integer"}},
    {"anyOf": [{"type": "string"}, {"type": "null"}]},
    {
        "type": "object",
        "properties": {"prop1": {"type": "string"}},
        "additionalProperties": False,
        "required": ["prop1"],
    },
    {
        "type": "object",
        "patternProperties": {"^.*$": {"type": "string"}},
    },
]

INVALID_SCHEMAS = [
    ({}, "unknown schema object: {}"),
    (
        {"type": "object", "properties": {}},
        "'additionalProperties' must be present on objects, and should probably be False (at schema)",
    ),
    (
        {
            "type": "object",
            "properties": {"prop1": {"type": "string"}},
            "additionalProperties": False,
        },
        '\'required\' must be present on objects, maybe you want: "required": ["prop1"] (at schema)',
    ),
    (
        {
            "type": "object",
            "properties": {"prop1": {"type": "string"}},
            "additionalProperties": False,
            "required": ["prop2"],
        },
        'required property "prop2" must be present in \'properties\', but it was not (at schema["required"][0])',
    ),
    (
        {
            "type": "object",
            "properties": {"prop1": {"type": "object", "properties": {}}},
            "additionalProperties": False,
            "required": ["prop1"],
        },
        '\'additionalProperties\' must be present on objects, and should probably be False (at schema["properties"]["prop1"])',
    ),
]


def test_validate_schema():
    for schema in VALID_SCHEMAS:
        validate_schema(schema)  # Shouldn't raise

    for schema, expected_error in INVALID_SCHEMAS:
        with pytest.raises(ValidationError) as error:
            validate_schema(schema)
        assert str(error.value) == expected_error
