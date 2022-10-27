# Formats a number using the appropriate singular or plural form of a noun.
def format_count(count: int, singular: str, plural: str) -> str:
    return f"{count:,} {singular if count == 1 else plural}"
