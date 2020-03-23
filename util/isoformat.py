import datetime
from typing import Optional, Union


def isoformat(
    datetime: Optional[Union[datetime.datetime, datetime.date]]
) -> Optional[str]:
    if datetime is not None:
        return datetime.isoformat()
    else:
        return None
