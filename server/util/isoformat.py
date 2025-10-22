import datetime


def isoformat(
    value: datetime.datetime | datetime.date | None,
) -> str | None:
    return value.isoformat() if value is not None else None
