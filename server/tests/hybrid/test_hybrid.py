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
