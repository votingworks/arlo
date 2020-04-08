import json
from flask.testing import FlaskClient
from typing import Generator
import pytest

from tests.helpers import assert_ok, post_json, create_election
from tests.test_app import setup_whole_audit
import bgcompute


@pytest.fixture()
def election_id(client: FlaskClient) -> Generator[str, None, None]:
    yield create_election(client, is_multi_jurisdiction=False)


def test_ballot_list_jurisdiction_two_rounds(client, election_id):
    (
        url_prefix,
        contest_id,
        candidate_id_1,
        candidate_id_2,
        jurisdiction_id,
        audit_board_id_1,
        audit_board_id_2,
        num_ballots,
    ) = setup_whole_audit(
        client, election_id, "Primary 2019", 10, "12345678901234567890"
    )

    # Get the sample size and round id
    rv = client.get(f"/election/{election_id}/audit/status")
    status = json.loads(rv.data)
    sample_size = status["rounds"][0]["contests"][0]["sampleSize"]
    round_id = status["rounds"][0]["id"]

    # Retrieve the ballot list
    rv = client.get(
        f"/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_id}/ballot-list"
    )
    ballot_list = json.loads(rv.data)["ballots"]
    assert ballot_list
    assert len(ballot_list) == sample_size

    # Post results for round 1 with 50/50 split, which should trigger a second round.
    num_for_winner = int(num_ballots * 0.5)
    num_for_loser = num_ballots - num_for_winner
    rv = post_json(
        client,
        "{}/jurisdiction/{}/1/results".format(url_prefix, jurisdiction_id),
        {
            "contests": [
                {
                    "id": contest_id,
                    "results": {
                        candidate_id_1: num_for_winner,
                        candidate_id_2: num_for_loser,
                    },
                }
            ]
        },
    )
    assert_ok(rv)
    bgcompute.bgcompute()

    # Get the sample size and round id for the second round
    rv = client.get(f"/election/{election_id}/audit/status")
    status = json.loads(rv.data)
    sample_size = status["rounds"][1]["contests"][0]["sampleSize"]
    round_id = status["rounds"][1]["id"]

    # Retrieve the ballot list
    rv = client.get(
        f"/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_id}/ballot-list"
    )
    ballot_list = json.loads(rv.data)["ballots"]
    assert ballot_list
    assert len(ballot_list) == sample_size


def test_ballot_list_audit_board_two_rounds(client, election_id):
    (
        url_prefix,
        contest_id,
        candidate_id_1,
        candidate_id_2,
        jurisdiction_id,
        audit_board_id_1,
        audit_board_id_2,
        num_ballots,
    ) = setup_whole_audit(
        client, election_id, "Primary 2019", 10, "12345678901234567890"
    )

    # Get the sample size and round id
    rv = client.get(f"/election/{election_id}/audit/status")
    status = json.loads(rv.data)
    sample_size = status["rounds"][0]["contests"][0]["sampleSize"]
    round_id = status["rounds"][0]["id"]

    # Retrieve the ballot lists (the ballots should be split b/w audit boards)
    ballot_list = []
    for audit_board_id in [audit_board_id_1, audit_board_id_2]:
        rv = client.get(
            f"/election/{election_id}/jurisdiction/{jurisdiction_id}/audit-board/{audit_board_id}/round/{round_id}/ballot-list"
        )
        board_ballot_list = json.loads(rv.data)["ballots"]
        assert board_ballot_list
        ballot_list += board_ballot_list

    assert len(ballot_list) == sample_size

    # Post results for round 1 with 50/50 split, which should trigger a second round.
    num_for_winner = int(num_ballots * 0.5)
    num_for_loser = num_ballots - num_for_winner
    rv = post_json(
        client,
        "{}/jurisdiction/{}/1/results".format(url_prefix, jurisdiction_id),
        {
            "contests": [
                {
                    "id": contest_id,
                    "results": {
                        candidate_id_1: num_for_winner,
                        candidate_id_2: num_for_loser,
                    },
                }
            ]
        },
    )
    assert_ok(rv)
    bgcompute.bgcompute()

    # Get the sample size and round id for the second round
    rv = client.get(f"/election/{election_id}/audit/status")
    status = json.loads(rv.data)
    sample_size = status["rounds"][1]["contests"][0]["sampleSize"]
    round_id = status["rounds"][1]["id"]

    # Retrieve the ballot lists (the ballots should be split b/w audit boards)
    ballot_list = []
    for audit_board_id in [audit_board_id_1, audit_board_id_2]:
        rv = client.get(
            f"/election/{election_id}/jurisdiction/{jurisdiction_id}/audit-board/{audit_board_id}/round/{round_id}/ballot-list"
        )
        board_ballot_list = json.loads(rv.data)["ballots"]
        assert board_ballot_list
        ballot_list += board_ballot_list

    assert len(ballot_list) == sample_size


def test_ballot_list_jurisdiction_ordering(client, election_id):
    (
        url_prefix,
        contest_id,
        candidate_id_1,
        candidate_id_2,
        jurisdiction_id,
        audit_board_id_1,
        audit_board_id_2,
        num_ballots,
    ) = setup_whole_audit(
        client, election_id, "Primary 2019", 10, "12345678901234567890"
    )

    # Get the round id
    rv = client.get(f"/election/{election_id}/audit/status")
    status = json.loads(rv.data)
    round_id = status["rounds"][0]["id"]

    # Verify that the ballots are ordered correctly
    rv = client.get(
        "{}/jurisdiction/{}/round/{}/ballot-list".format(
            url_prefix, jurisdiction_id, round_id
        )
    )
    unsorted_ballots = json.loads(rv.data)["ballots"]
    sorted_ballots = sorted(
        unsorted_ballots,
        key=lambda ballot: (
            ballot["auditBoard"]["name"],
            ballot["batch"]["name"],
            ballot["position"],
        ),
    )

    assert unsorted_ballots == sorted_ballots


def test_ballot_list_audit_board_ordering(client, election_id):
    (
        url_prefix,
        contest_id,
        candidate_id_1,
        candidate_id_2,
        jurisdiction_id,
        audit_board_id_1,
        audit_board_id_2,
        num_ballots,
    ) = setup_whole_audit(
        client, election_id, "Primary 2019", 10, "12345678901234567890"
    )

    # Get the round id
    rv = client.get(f"/election/{election_id}/audit/status")
    status = json.loads(rv.data)
    round_id = status["rounds"][0]["id"]

    # Verify that the ballots are ordered correctly
    for audit_board_id in [audit_board_id_1, audit_board_id_2]:
        rv = client.get(
            "{}/jurisdiction/{}/audit-board/{}/round/{}/ballot-list".format(
                url_prefix, jurisdiction_id, audit_board_id, round_id
            )
        )
        unsorted_ballots = json.loads(rv.data)["ballots"]
        sorted_ballots = sorted(
            unsorted_ballots,
            key=lambda ballot: (ballot["batch"]["name"], ballot["position"]),
        )

        assert unsorted_ballots == sorted_ballots
