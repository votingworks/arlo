import datetime
from typing import Optional, Union


def isoformat(
    value: Optional[Union[datetime.datetime, datetime.date]],
) -> Optional[str]:
    return value.isoformat() if value is not None else None
