import re
from datetime import datetime
from flask import Response

from ..models import *  # pylint: disable=wildcard-import


def election_timestamp_name(election: Election) -> str:
    clean_election_name = re.sub(r"[^a-zA-Z0-9]+", r"-", str(election.election_name))
    now = datetime.utcnow().isoformat(timespec="minutes")
    return f"{clean_election_name}-{now}"


def csv_response(csv_text: str, filename: str) -> Response:
    return Response(
        csv_text,
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
