import re
from datetime import datetime
from flask import Response

from ..models import *  # pylint: disable=wildcard-import

clean_name_re = re.compile(r"[^a-zA-Z0-9]+")


def election_timestamp_name(election: Election) -> str:
    election_name = re.sub(clean_name_re, "-", str(election.audit_name))
    now = datetime.utcnow().isoformat(timespec="minutes")
    return f"{election_name}-{now}"


def jurisdiction_timestamp_name(election: Election, jurisdiction: Jurisdiction) -> str:
    election_name = re.sub(clean_name_re, "-", str(election.audit_name))
    jurisdiction_name = re.sub(clean_name_re, "-", str(jurisdiction.name))
    now = datetime.utcnow().isoformat(timespec="minutes")
    return f"{jurisdiction_name}-{election_name}-{now}"


def csv_response(csv_text: str, filename: str) -> Response:
    return Response(
        csv_text,
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
