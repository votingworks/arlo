from typing import Optional


# Formats a number using the appropriate singular or plural form of a noun.
def format_count(count: int, singular: str, plural: str) -> str:
    return f"{count:,} {singular if count == 1 else plural}"


# Returns `value.strip()` or None if `value` is None
def strip_optional_string(value: Optional[str]) -> str:
    return (value or "").strip()
