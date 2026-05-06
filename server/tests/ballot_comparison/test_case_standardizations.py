import io
import json
import typing
import uuid

import pytest
from flask.testing import FlaskClient
from werkzeug.wrappers import Response

from ...api.contests import unique_case_insensitive_match
from ...auth.auth_helpers import UserType
from ..helpers import (
    DEFAULT_AA_EMAIL,
    assert_ok,
    set_logged_in_user,
    upload_standardized_contests,
)


def test_case_insensitive_match_does_not_guess_when_ambiguous():
    assert (
        unique_case_insensitive_match("Contest 1", ["CONTEST 1", "contest 1"]) is None
    )


@pytest.mark.usefixtures("election_settings", "manifests", "cvrs")
def test_standardize_contest_names_prepopulates_case_insensitive_matches(
    client: FlaskClient, election_id: str, jurisdiction_ids: list[str]
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    contests = [
        {
            "id": str(uuid.uuid4()),
            "name": "CONTEST 1",
            "isTargeted": True,
            "numWinners": 1,
            "jurisdictionIds": jurisdiction_ids[:1],
        },
    ]
    rv = typing.cast(
        Response,
        client.put(
            f"/api/election/{election_id}/contest",
            headers={"Content-Type": "application/json"},
            data=json.dumps(contests),
        ),
    )
    assert_ok(rv)

    rv = typing.cast(
        Response, client.get(f"/api/election/{election_id}/contest/standardizations")
    )
    assert rv.status_code == 200
    assert json.loads(typing.cast(bytes, rv.data).decode("utf-8")) == {
        "standardizations": {
            jurisdiction_ids[0]: {"CONTEST 1": "Contest 1"},
        },
        "cvrContestNames": {jurisdiction_ids[0]: ["Contest 1", "Contest 2"]},
    }


@pytest.mark.usefixtures("election_settings", "manifests", "cvrs")
def test_standardize_contest_choice_names_prepopulates_case_insensitive_matches(
    client: FlaskClient, election_id: str, jurisdiction_ids: list[str]
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = typing.cast(
        Response,
        upload_standardized_contests(
            client,
            io.BytesIO(
                b"Contest Name,Jurisdictions,Choice Names\n"
                + b'Contest 1,J1,"CHOICE 1-1;Choice 1-2"\n'
            ),
            election_id,
        ),
    )
    assert_ok(rv)

    contest_id = str(uuid.uuid4())
    contests = [
        {
            "id": contest_id,
            "name": "Contest 1",
            "isTargeted": True,
            "numWinners": 1,
            "jurisdictionIds": jurisdiction_ids[:1],
        },
    ]
    rv = typing.cast(
        Response,
        client.put(
            f"/api/election/{election_id}/contest",
            headers={"Content-Type": "application/json"},
            data=json.dumps(contests),
        ),
    )
    assert_ok(rv)

    rv = typing.cast(
        Response,
        client.get(f"/api/election/{election_id}/contest/choice-name-standardizations"),
    )
    assert rv.status_code == 200
    assert json.loads(typing.cast(bytes, rv.data).decode("utf-8")) == {
        "standardizations": {
            jurisdiction_ids[0]: {contest_id: {"Choice 1-1": "CHOICE 1-1"}},
            jurisdiction_ids[1]: {contest_id: {"Choice 1-1": "CHOICE 1-1"}},
        }
    }
