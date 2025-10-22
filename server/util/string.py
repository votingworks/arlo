# Formats a number using the appropriate singular or plural form of a noun.
def format_count(count: int, singular: str, plural: str) -> str:
    return f"{count:,} {singular if count == 1 else plural}"


# Returns `value.strip()` or None if `value` is None
def strip_optional_string(value: str | None) -> str:
    return (value or "").strip()


# Joins a list of strings with commas up to a limit, then lists the remaining count.
def comma_join_until_limit(items: list[str], limit: int) -> str:
    num_over_limit = len(items) - limit
    items_to_join = items[:limit]
    if num_over_limit > 0:
        items_to_join.append(f"and {num_over_limit:,} more")
    return ", ".join(items_to_join)
