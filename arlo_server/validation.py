from werkzeug.exceptions import BadRequest
from typing import List, NoReturn


def check_required_fields(json: dict, fields: List[str], prefix: str = "") -> None:
    missing_field = next((field for field in fields if field not in json), None)
    if missing_field:
        raise BadRequest(f"Missing required field {prefix}{missing_field}")


def check_required_fields_for_contest(json: dict) -> None:
    check_required_fields(
        json,
        ["id", "name", "isTargeted", "totalBallotsCast", "numWinners", "votesAllowed",],
        "contest.",
    )
