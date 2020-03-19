from typing import Any, Dict, List

JSONSchema = Any
Str = {"type": "string"}
Int = {"type": "integer"}
Bool = {"type": "boolean"}


def nullable(schema: JSONSchema) -> JSONSchema:
    return {"anyOf": [schema, {"type": "null"}]}


def Obj(**properties: Dict[str, JSONSchema]) -> JSONSchema:
    return {
        "type": "object",
        "properties": properties,
        "additionalProperties": False,
        "required": list(properties.keys()),
    }


def Enum(values: List[str]) -> JSONSchema:
    return {
        "type": "string",
        "enum": values,
    }


def IntRange(
    minimum: int, maximum: int, exclusiveMaximum=False, exclusiveMinimum=False
):
    if exclusiveMinimum:
        minimum += 1
    if exclusiveMaximum:
        maximum -= 1

    assert minimum <= maximum
    return {
        "type": "integer",
        "minimum": minimum,
        "maximum": maximum,
    }
