import json
from ...models import *  # pylint: disable=wildcard-import
from ..helpers import *  # pylint: disable=wildcard-import


def test_contest_vote_counts_before_cvrs(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    contest_ids: List[str],  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/contest")
    contests = json.loads(rv.data)["contests"]
    # Returns None for numVotesCvr/NonCvr before CVRs are uploaded
    compare_json(
        contests[0]["choices"],
        [
            {
                "id": assert_is_id,
                "name": "Choice 1-1",
                "numVotes": 14 + 16,  # CVR + non-CVR
                "numVotesCvr": None,
                "numVotesNonCvr": None,
            },
            {
                "id": assert_is_id,
                "name": "Choice 1-2",
                "numVotes": 8 + 4,
                "numVotesCvr": None,
                "numVotesNonCvr": None,
            },
        ],
    )
    compare_json(
        contests[1]["choices"],
        [
            {
                "id": assert_is_id,
                "name": "Choice 2-1",
                "numVotes": 14 + 6,
                "numVotesCvr": None,
                "numVotesNonCvr": None,
            },
            {
                "id": assert_is_id,
                "name": "Choice 2-2",
                "numVotes": 6 + 2,
                "numVotesCvr": None,
                "numVotesNonCvr": None,
            },
            {
                "id": assert_is_id,
                "name": "Choice 2-3",
                "numVotes": 8 + 2,
                "numVotesCvr": None,
                "numVotesNonCvr": None,
            },
        ],
    )


def test_contest_vote_counts(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    contest_ids: List[str],  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    cvrs,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/contest")
    contests = json.loads(rv.data)["contests"]
    compare_json(
        contests[0]["choices"],
        [
            {
                "id": assert_is_id,
                "name": "Choice 1-1",
                "numVotes": 12 + 18,  # CVR + non-CVR
                "numVotesCvr": 12,
                "numVotesNonCvr": 18,
            },
            {
                "id": assert_is_id,
                "name": "Choice 1-2",
                "numVotes": 8 + 4,
                "numVotesCvr": 8,
                "numVotesNonCvr": 4,
            },
        ],
    )
    compare_json(
        contests[1]["choices"],
        [
            {
                "id": assert_is_id,
                "name": "Choice 2-1",
                "numVotes": 13 + 7,
                "numVotesCvr": 13,
                "numVotesNonCvr": 7,
            },
            {
                "id": assert_is_id,
                "name": "Choice 2-2",
                "numVotes": 6 + 2,
                "numVotesCvr": 6,
                "numVotesNonCvr": 2,
            },
            {
                "id": assert_is_id,
                "name": "Choice 2-3",
                "numVotes": 7 + 3,
                "numVotesCvr": 7,
                "numVotesNonCvr": 3,
            },
        ],
    )


def test_sample_size(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    contest_ids: List[str],  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    cvrs,  # pylint: disable=unused-argument
    snapshot,
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/sample-sizes")
    sample_sizes = json.loads(rv.data)["sampleSizes"]
    assert len(sample_sizes) == 1
    snapshot.assert_match(sample_sizes[contest_ids[0]])


def test_sample_size_before_manifest(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    contest_ids: List[str],  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/sample-sizes")
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Conflict",
                "message": "Some jurisdictions haven't uploaded their manifests yet",
            }
        ]
    }


def test_sample_size_before_cvrs(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    contest_ids: List[str],  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/sample-sizes")
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Conflict",
                "message": "Some jurisdictions haven't uploaded their CVRs yet.",
            }
        ]
    }


def test_contest_names_dont_match_cvrs(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    contest_ids: List[str],  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    cvrs,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    contests = [
        {
            "id": str(uuid.uuid4()),
            "name": "Bad Contest Name",
            "isTargeted": True,
            "choices": [
                {"id": str(uuid.uuid4()), "name": "Choice 1-1", "numVotes": 1},
                {"id": str(uuid.uuid4()), "name": "Choice 1-2", "numVotes": 2},
            ],
            "numWinners": 1,
            "votesAllowed": 1,
            "jurisdictionIds": jurisdiction_ids[:2],
        },
    ]
    rv = put_json(client, f"/api/election/{election_id}/contest", contests)
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/sample-sizes")
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Conflict",
                "message": "Couldn't find contest Bad Contest Name in the CVR for jurisdiction J1",
            }
        ]
    }


def test_contest_choices_dont_match_cvrs(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    contest_ids: List[str],  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    cvrs,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    contests = [
        {
            "id": str(uuid.uuid4()),
            "name": "Contest 1",
            "isTargeted": True,
            "choices": [
                {"id": str(uuid.uuid4()), "name": "Bad Choice Name", "numVotes": 1,},
                {"id": str(uuid.uuid4()), "name": "Choice 1-2", "numVotes": 2},
                {
                    "id": str(uuid.uuid4()),
                    "name": "Another Bad Choice Name",
                    "numVotes": 1,
                },
            ],
            "numWinners": 1,
            "votesAllowed": 1,
            "jurisdictionIds": jurisdiction_ids[:2],
        },
    ]
    rv = put_json(client, f"/api/election/{election_id}/contest", contests)
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/sample-sizes")
    assert rv.status_code == 409
    assert json.loads(rv.data) == {
        "errors": [
            {
                "errorType": "Conflict",
                "message": "Couldn't find some contest choices (Another Bad Choice Name, Bad Choice Name) in the CVR for jurisdiction J1",
            }
        ]
    }
