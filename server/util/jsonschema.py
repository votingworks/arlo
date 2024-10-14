import re
from typing import Any, Dict, List, Union
import jsonschema
import jsonschema.validators


# An approximation of a JSON object type, since mypy doesn't support
# recursive types.
JSONDict = Dict[str, Any]
JSONSchema = JSONDict

# https://emailregex.com/
EMAIL_REGEX = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")

# The built-in checker for email just checks if there's an @ in the string
jsonschema.draft7_format_checker.checkers["email"] = (
    lambda value: EMAIL_REGEX.match(value) is not None,
    (),
)


def validate(instance: Any, schema: JSONSchema):
    jsonschema.validators.validator_for(schema).check_schema(schema)
    validate_schema(schema)
    jsonschema.validate(
        instance=instance,
        schema=schema,
        format_checker=jsonschema.draft7_format_checker,
    )


def validate_schema(schema: JSONSchema):
    def validate_schema_node(node: JSONSchema, current_keypath: List[Union[str, int]]):
        assert isinstance(node, dict)
        if node.get("type", None) == "object":
            properties = node.get("properties", None)
            pattern_properties = node.get("patternProperties", None)

            if properties is not None:
                assert isinstance(properties, dict)

                if "additionalProperties" not in node:
                    raise jsonschema.exceptions.ValidationError(
                        f"'additionalProperties' must be present on objects, and should probably be False (at {_serialize_keypath(current_keypath)})"
                    )

                if "required" not in node:
                    missing_keys = "".join(f'"{key}"' for key in properties)
                    hint = f'"required": [{missing_keys}]'
                    raise jsonschema.exceptions.ValidationError(
                        f"'required' must be present on objects, maybe you want: {hint} (at {_serialize_keypath(current_keypath)})"
                    )

                for index, key in enumerate(node["required"]):
                    if key not in properties:
                        raise jsonschema.exceptions.ValidationError(
                            f"required property \"{key}\" must be present in 'properties', but it was not (at {_serialize_keypath(current_keypath + ['required', index])})"
                        )

                for key, prop in properties.items():
                    validate_schema_node(prop, current_keypath + ["properties", key])

            if pattern_properties is not None:
                assert isinstance(pattern_properties, dict)
                for key, prop in pattern_properties.items():
                    validate_schema_node(
                        prop, current_keypath + ["patternProperties", key]
                    )
        elif node.get("type", None) == "array":
            validate_schema_node(node["items"], current_keypath + ["items"])
        elif "anyOf" in node:
            for index, element in enumerate(node["anyOf"]):
                validate_schema_node(element, current_keypath + ["anyOf", index])
        elif node.get("type", None) in ["string", "boolean", "integer", "null"]:
            pass
        else:
            raise jsonschema.exceptions.ValidationError(
                f"unknown schema object: {node}"
            )

    validate_schema_node(schema, [])


def _serialize_key(key: Union[str, int]):
    if isinstance(key, str):
        return f'"{key}"'
    else:
        return f"{key}"


def _serialize_keypath(keypath: List[Union[str, int]]):
    return f"schema{''.join(f'[{_serialize_key(key)}]' for key in keypath)}"
