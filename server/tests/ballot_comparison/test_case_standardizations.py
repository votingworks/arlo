import io
import json
import typing
import uuid

import pytest
from flask.testing import FlaskClient
from werkzeug.wrappers import Response

from ..helpers import (
    DEFAULT_AA_EMAIL,
    UserType,
    assert_ok,
    put_json,
    set_logged_in_user,
    upload_standardized_contests,
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
        Response, put_json(client, f"/api/election/{election_id}/contest", contests)
    )
    assert_ok(rv)

    rv = typing.cast(
        Response, client.get(f"/api/election/{election_id}/contest/standardizations")
    )
    assert rv.status_code == 200
    assert json.loads(rv.data) == {
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
                b'Contest 1,J1,"CHOICE 1-1;Choice 1-2"\n'
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
        Response, put_json(client, f"/api/election/{election_id}/contest", contests)
    )
    assert_ok(rv)

    rv = typing.cast(
        Response,
        client.get(f"/api/election/{election_id}/contest/choice-name-standardizations"),
    )
    assert rv.status_code == 200
    assert json.loads(rv.data) == {
        "standardizations": {
            jurisdiction_ids[0]: {contest_id: {"Choice 1-1": "CHOICE 1-1"}},
            jurisdiction_ids[1]: {contest_id: {"Choice 1-1": "CHOICE 1-1"}},
        }
    }
