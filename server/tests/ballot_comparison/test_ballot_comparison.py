from collections import Counter
import io
import json
import csv
from flask.testing import FlaskClient
from sqlalchemy import and_

from ...models import *  # pylint: disable=wildcard-import
from ..helpers import *  # pylint: disable=wildcard-import
from .conftest import (
    TEST_CVRS,
    TEST_CVRS_WITH_CHOICE_REMOVED,
    TEST_CVRS_WITH_EXTRA_CHOICE,
)
from ..ballot_comparison.test_cvrs import (
    ESS_BALLOTS_1,
    ESS_BALLOTS_2,
)


def test_set_contest_metadata_on_contest_creation(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    cvrs,  # pylint: disable=unused-argument
    snapshot,
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    contest_id = str(uuid.uuid4())
    rv = put_json(
        client,
        f"/api/election/{election_id}/contest",
        [
            {
                "id": contest_id,
                "name": "Contest 2",
                "numWinners": 1,
                "jurisdictionIds": jurisdiction_ids[:2],
                "isTargeted": True,
            }
        ],
    )
    assert_ok(rv)

    # Contest metadata is set on contest creation when all manifests and CVRs uploaded
    contest = Contest.query.get(contest_id)
    snapshot.assert_match(
        dict(
            # Set from manifest
            total_ballots_cast=contest.total_ballots_cast,
            # Set from CVRs
            votes_allowed=contest.votes_allowed,
            choices=[
                dict(name=choice.name, num_votes=choice.num_votes)
                for choice in contest.choices
            ],
        )
    )


def test_set_contest_metadata_on_manifest_and_cvr_upload(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    contest_id = str(uuid.uuid4())
    rv = put_json(
        client,
        f"/api/election/{election_id}/contest",
        [
            {
                "id": contest_id,
                "name": "Contest 2",
                "numWinners": 1,
                "jurisdictionIds": jurisdiction_ids[:2],
                "isTargeted": True,
            }
        ],
    )
    assert_ok(rv)

    # Contest metadata isn't set when creating contest if no manifest/CVRs
    rv = client.get(f"/api/election/{election_id}/contest")
    contest = json.loads(rv.data)["contests"][0]
    assert contest["choices"] == []
    assert contest["totalBallotsCast"] is None
    assert contest["votesAllowed"] is None

    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest",
        data={
            "manifest": (
                io.BytesIO(
                    b"Tabulator,Batch Name,Number of Ballots\n"
                    b"TABULATOR1,BATCH1,3\n"
                    b"TABULATOR1,BATCH2,3\n"
                    b"TABULATOR2,BATCH1,3\n"
                    b"TABULATOR2,BATCH2,6"
                ),
                "manifest.csv",
            )
        },
    )
    assert_ok(rv)

    # Contest total ballots isn't set when only some manifests uploaded
    rv = client.get(f"/api/election/{election_id}/contest")
    contest = json.loads(rv.data)["contests"][0]
    assert contest["choices"] == []
    assert contest["totalBallotsCast"] is None
    assert contest["votesAllowed"] is None

    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/ballot-manifest",
        data={
            "manifest": (
                io.BytesIO(
                    b"Tabulator,Batch Name,Number of Ballots\n"
                    b"TABULATOR1,BATCH1,3\n"
                    b"TABULATOR1,BATCH2,3\n"
                    b"TABULATOR2,BATCH1,3\n"
                    b"TABULATOR2,BATCH2,6"
                ),
                "manifest.csv",
            )
        },
    )
    assert_ok(rv)

    # Contest total ballots is set when all manifests uploaded
    rv = client.get(f"/api/election/{election_id}/contest")
    contest = json.loads(rv.data)["contests"][0]
    assert contest["choices"] == []
    assert contest["totalBallotsCast"] == 30
    assert contest["votesAllowed"] is None

    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs",
        data={
            "cvrs": (
                io.BytesIO(TEST_CVRS.encode()),
                "cvrs.csv",
            ),
            "cvrFileType": "DOMINION",
        },
    )
    assert_ok(rv)

    # Contest votes allowed/choices isn't set when only some CVRs uploaded
    rv = client.get(f"/api/election/{election_id}/contest")
    contest = json.loads(rv.data)["contests"][0]
    assert contest["choices"] == []
    assert contest["totalBallotsCast"] == 30
    assert contest["votesAllowed"] is None

    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/cvrs",
        data={
            "cvrs": (
                io.BytesIO(TEST_CVRS.encode()),
                "cvrs.csv",
            ),
            "cvrFileType": "DOMINION",
        },
    )
    assert_ok(rv)

    # Contest votes allowed/choices is set when all CVRs uploaded
    rv = client.get(f"/api/election/{election_id}/contest")
    contest = json.loads(rv.data)["contests"][0]
    assert [
        {"name": choice["name"], "numVotes": choice["numVotes"]}
        for choice in contest["choices"]
    ] == [
        {"name": "Choice 2-1", "numVotes": 24},
        {"name": "Choice 2-2", "numVotes": 10},
        {"name": "Choice 2-3", "numVotes": 14},
    ]
    assert contest["totalBallotsCast"] == 30
    assert contest["votesAllowed"] == 2

    #
    # Contest metadata changes on new manifest/CVR upload
    #

    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest",
        data={
            "manifest": (
                io.BytesIO(
                    b"Tabulator,Batch Name,Number of Ballots\n"
                    b"TABULATOR1,BATCH1,3\n"
                    b"TABULATOR1,BATCH2,3\n"
                    b"TABULATOR2,BATCH1,3"
                ),
                "manifest.csv",
            )
        },
    )
    assert_ok(rv)

    new_cvr = "\n".join(TEST_CVRS.splitlines()[:10])
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs",
        data={
            "cvrs": (
                io.BytesIO(new_cvr.encode()),
                "cvrs.csv",
            ),
            "cvrFileType": "DOMINION",
        },
    )
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/contest")
    contest = json.loads(rv.data)["contests"][0]
    assert [
        {"name": choice["name"], "numVotes": choice["numVotes"]}
        for choice in contest["choices"]
    ] == [
        {"name": "Choice 2-1", "numVotes": 18},
        {"name": "Choice 2-2", "numVotes": 8},
        {"name": "Choice 2-3", "numVotes": 10},
    ]
    assert contest["totalBallotsCast"] == 24
    assert contest["votesAllowed"] == 2


def test_cvr_choice_name_validation(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    manifests,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    contest_id = str(uuid.uuid4())
    rv = put_json(
        client,
        f"/api/election/{election_id}/contest",
        [
            {
                "id": contest_id,
                "isTargeted": True,
                "jurisdictionIds": jurisdiction_ids[:2],
                "name": "Contest 1",
                "numWinners": 1,
            }
        ],
    )
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/contest")
    contest = json.loads(rv.data)["contests"][0]
    assert "cvrChoiceNameConsistencyError" not in contest

    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs",
        data={
            "cvrs": (
                io.BytesIO(TEST_CVRS.encode()),
                "cvrs.csv",
            ),
            "cvrFileType": "DOMINION",
        },
    )
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/contest")
    contest = json.loads(rv.data)["contests"][0]
    assert "cvrChoiceNameConsistencyError" not in contest

    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/cvrs",
        data={
            "cvrs": (
                io.BytesIO(TEST_CVRS.encode()),
                "cvrs.csv",
            ),
            "cvrFileType": "DOMINION",
        },
    )
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/contest")
    contest = json.loads(rv.data)["contests"][0]
    assert "cvrChoiceNameConsistencyError" not in contest

    modified_cvrs = TEST_CVRS.replace("Choice", "CHOICE")
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/cvrs",
        data={
            "cvrs": (
                io.BytesIO(modified_cvrs.encode()),
                "cvrs.csv",
            ),
            "cvrFileType": "DOMINION",
        },
    )
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/contest")
    contest = json.loads(rv.data)["contests"][0]
    assert contest["cvrChoiceNameConsistencyError"] == {
        "anomalousCvrChoiceNamesByJurisdiction": {
            jurisdiction_ids[1]: ["CHOICE 1-1", "CHOICE 1-2"],
        },
        "cvrChoiceNamesInJurisdictionWithMostCvrChoices": [
            "Choice 1-1",
            "Choice 1-2",
        ],
        "jurisdictionIdWithMostCvrChoices": jurisdiction_ids[0],
    }

    modified_cvrs = TEST_CVRS.replace("Choice 1-1", "CHOICE 1-1")
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/cvrs",
        data={
            "cvrs": (
                io.BytesIO(modified_cvrs.encode()),
                "cvrs.csv",
            ),
            "cvrFileType": "DOMINION",
        },
    )
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/contest")
    contest = json.loads(rv.data)["contests"][0]
    assert contest["cvrChoiceNameConsistencyError"] == {
        "anomalousCvrChoiceNamesByJurisdiction": {
            jurisdiction_ids[1]: ["CHOICE 1-1"],
        },
        "cvrChoiceNamesInJurisdictionWithMostCvrChoices": [
            "Choice 1-1",
            "Choice 1-2",
        ],
        "jurisdictionIdWithMostCvrChoices": jurisdiction_ids[0],
    }

    modified_cvrs = TEST_CVRS_WITH_CHOICE_REMOVED
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/cvrs",
        data={
            "cvrs": (
                io.BytesIO(modified_cvrs.encode()),
                "cvrs.csv",
            ),
            "cvrFileType": "DOMINION",
        },
    )
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/contest")
    contest = json.loads(rv.data)["contests"][0]
    assert "cvrChoiceNameConsistencyError" not in contest

    modified_cvrs = TEST_CVRS_WITH_EXTRA_CHOICE
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/cvrs",
        data={
            "cvrs": (
                io.BytesIO(modified_cvrs.encode()),
                "cvrs.csv",
            ),
            "cvrFileType": "DOMINION",
        },
    )
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/contest")
    contest = json.loads(rv.data)["contests"][0]
    assert "cvrChoiceNameConsistencyError" not in contest


def test_set_contest_metadata_on_jurisdiction_change(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    cvrs,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    contest_id = str(uuid.uuid4())
    rv = put_json(
        client,
        f"/api/election/{election_id}/contest",
        [
            {
                "id": contest_id,
                "name": "Contest 2",
                "numWinners": 1,
                "jurisdictionIds": jurisdiction_ids[:2],
                "isTargeted": True,
            }
        ],
    )
    assert_ok(rv)

    # Contest metadata is set
    rv = client.get(f"/api/election/{election_id}/contest")
    original_contest = json.loads(rv.data)["contests"][0]
    assert original_contest["totalBallotsCast"] is not None
    assert original_contest["votesAllowed"] is not None
    assert original_contest["choices"] != []

    # Upload new jurisdictions, removing J1
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/file",
        data={
            "jurisdictions": (
                io.BytesIO(
                    (
                        "Jurisdiction,Admin Email\n"
                        f"J2,{default_ja_email(election_id)}\n"
                        f"J3,j3-{election_id}@example.com\n"
                    ).encode()
                ),
                "jurisdictions.csv",
            )
        },
    )
    assert_ok(rv)

    # Contest universe and metadata changes
    rv = client.get(f"/api/election/{election_id}/contest")
    contest = json.loads(rv.data)["contests"][0]
    assert contest["jurisdictionIds"] == [jurisdiction_ids[1]]
    assert contest["totalBallotsCast"] == original_contest["totalBallotsCast"] / 2
    assert contest["votesAllowed"] == original_contest["votesAllowed"]
    assert (
        contest["choices"][0]["numVotes"]
        == original_contest["choices"][0]["numVotes"] / 2
    )


def test_require_cvr_uploads(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)

    # AA creates contests
    rv = put_json(
        client,
        f"/api/election/{election_id}/contest",
        [
            {
                "id": str(uuid.uuid4()),
                "name": "Contest 1",
                "numWinners": 1,
                "jurisdictionIds": jurisdiction_ids[:2],
                "isTargeted": True,
            },
        ],
    )
    assert_ok(rv)

    # AA tries to select a sample size - should get an error because CVRs have
    # to be uploaded first
    rv = client.get(f"/api/election/{election_id}/sample-sizes/1")
    assert rv.status_code == 200
    compare_json(
        json.loads(rv.data),
        {
            "sampleSizes": None,
            "selected": None,
            "task": {
                "status": "ERRORED",
                "startedAt": assert_is_date,
                "completedAt": assert_is_date,
                "error": "Some jurisdictions haven't uploaded their CVRs yet.",
            },
        },
    )


def test_require_manifest_uploads(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)

    # AA creates contests
    rv = put_json(
        client,
        f"/api/election/{election_id}/contest",
        [
            {
                "id": str(uuid.uuid4()),
                "name": "Contest 1",
                "numWinners": 1,
                "jurisdictionIds": jurisdiction_ids[:2],
                "isTargeted": True,
            },
        ],
    )
    assert_ok(rv)

    # AA tries to select a sample size - should get an error because manifests have
    # to be uploaded first
    rv = client.get(f"/api/election/{election_id}/sample-sizes/1")
    assert rv.status_code == 200
    compare_json(
        json.loads(rv.data),
        {
            "sampleSizes": None,
            "selected": None,
            "task": {
                "status": "ERRORED",
                "startedAt": assert_is_date,
                "completedAt": assert_is_date,
                "error": "Some jurisdictions haven't uploaded their manifests yet",
            },
        },
    )


def test_contest_names_dont_match_cvr_contests(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
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
            "numWinners": 1,
            "jurisdictionIds": jurisdiction_ids[:2],
        },
    ]
    rv = put_json(client, f"/api/election/{election_id}/contest", contests)
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/sample-sizes/1")
    assert rv.status_code == 200
    compare_json(
        json.loads(rv.data),
        {
            "sampleSizes": None,
            "selected": None,
            "task": {
                "status": "ERRORED",
                "startedAt": assert_is_date,
                "completedAt": assert_is_date,
                "error": "Couldn't find contest Bad Contest Name in the CVR for jurisdiction J1",
            },
        },
    )


def ballot_key(ballot: SampledBallot):
    return (
        ballot.batch.jurisdiction.name,
        ballot.batch.tabulator,
        ballot.batch.name,
        ballot.ballot_position,
    )


def audit_all_ballots(
    round_id: str,
    audit_results,
    target_contest_id,
    opportunistic_contest_id,
    invalid_write_in_ratio=0.1,
):
    choice_1_1, choice_1_2, *_ = sorted(
        Contest.query.get(target_contest_id).choices,
        key=lambda choice: str(choice.name),
    )
    choice_2_1, choice_2_2, choice_2_3, *_ = sorted(
        Contest.query.get(opportunistic_contest_id).choices,
        key=lambda choice: str(choice.name),
    )

    round = Round.query.get(round_id)
    sampled_ballots = (
        SampledBallot.query.filter_by(status=BallotStatus.NOT_AUDITED)
        .join(SampledBallotDraw)
        .filter_by(round_id=round.id)
        .join(Batch)
        .order_by(Batch.tabulator, Batch.name, SampledBallot.ballot_position)
        .all()
    )
    sampled_ballot_keys = [ballot_key(ballot) for ballot in sampled_ballots]

    assert sorted(sampled_ballot_keys) == sorted(list(audit_results.keys()))

    num_sampled_ballots = len(sampled_ballots)
    for i, ballot in enumerate(sampled_ballots):
        interpretation_str, _ = audit_results[ballot_key(ballot)]
        has_invalid_write_in = i < num_sampled_ballots * invalid_write_in_ratio

        if interpretation_str == "not found":
            ballot.status = BallotStatus.NOT_FOUND
            continue

        ballot.status = BallotStatus.AUDITED

        if interpretation_str == "blank":
            audit_ballot(
                ballot,
                target_contest_id,
                Interpretation.BLANK,
                has_invalid_write_in=has_invalid_write_in,
            )
            audit_ballot(
                ballot,
                opportunistic_contest_id,
                Interpretation.BLANK,
                has_invalid_write_in=has_invalid_write_in,
            )

        elif interpretation_str == "not on ballot":
            audit_ballot(
                ballot,
                target_contest_id,
                Interpretation.CONTEST_NOT_ON_BALLOT,
            )
            audit_ballot(
                ballot,
                opportunistic_contest_id,
                Interpretation.CONTEST_NOT_ON_BALLOT,
            )

        else:
            (
                vote_choice_1_1,
                vote_choice_1_2,
                vote_choice_2_1,
                vote_choice_2_2,
                vote_choice_2_3,
            ) = interpretation_str.split(",")

            target_choices = ([choice_1_1] if vote_choice_1_1 == "1" else []) + (
                [choice_1_2] if vote_choice_1_2 == "1" else []
            )
            audit_ballot(
                ballot,
                target_contest_id,
                (
                    Interpretation.CONTEST_NOT_ON_BALLOT
                    if vote_choice_1_1 == ""
                    else (
                        Interpretation.BLANK
                        if len(target_choices) == 0
                        else Interpretation.VOTE
                    )
                ),
                target_choices,
                has_invalid_write_in=has_invalid_write_in,
            )

            opportunistic_choices = (
                ([choice_2_1] if vote_choice_2_1 == "1" else [])
                + ([choice_2_2] if vote_choice_2_2 == "1" else [])
                + ([choice_2_3] if vote_choice_2_3 == "1" else [])
            )
            audit_ballot(
                ballot,
                opportunistic_contest_id,
                (
                    Interpretation.CONTEST_NOT_ON_BALLOT
                    if vote_choice_2_1 == ""
                    else (
                        Interpretation.BLANK
                        if len(opportunistic_choices) == 0
                        else Interpretation.VOTE
                    )
                ),
                opportunistic_choices,
                has_invalid_write_in=has_invalid_write_in,
            )


# Check expected discrepancies against audit report
def check_discrepancies(report: str, audit_results):
    def parse_discrepancy(discrepancy: str):
        return int(discrepancy) if discrepancy != "" else None

    report_ballots = list(csv.DictReader(io.StringIO(report)))
    for ballot, (_, expected_discrepancies) in audit_results.items():
        jurisdiction, tabulator, batch, position = ballot
        row = next(
            row
            for row in report_ballots
            if row["Jurisdiction Name"] == jurisdiction
            and row["Tabulator"] == tabulator
            and row["Batch Name"] == batch
            and row["Ballot Position"] == str(position)
        )
        assert (
            parse_discrepancy(row["Change in Margin: Contest 1"]),
            parse_discrepancy(row["Change in Margin: Contest 2"]),
        ) == expected_discrepancies, f"Discrepancy mismatch for {ballot}"


# Counts the expected discrepancies in the audit results by jurisdiction
def count_discrepancies(audit_results):
    count = Counter()
    for ballot, (_, expected_discrepancies) in audit_results.items():
        jurisdiction_name, _, _, _ = ballot
        count[jurisdiction_name] += len(
            [
                discrepancy
                for discrepancy in expected_discrepancies
                if discrepancy is not None
            ]
        )
    return count


def test_ballot_comparison_two_rounds(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    cvrs,  # pylint: disable=unused-argument
    snapshot,
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)

    # AA uploads standardized contests file
    rv = client.put(
        f"/api/election/{election_id}/standardized-contests/file",
        data={
            "standardized-contests": (
                io.BytesIO(
                    b"Contest Name,Jurisdictions\n"
                    b'Contest 1,"J1,J2"\n'
                    b'Contest 2,"J1,J2"\n'
                    b"Contest 3,J2\n"
                ),
                "standardized-contests.csv",
            )
        },
    )
    assert_ok(rv)

    # AA selects a contest to target from the standardized contest list
    rv = client.get(f"/api/election/{election_id}/standardized-contests")
    standardized_contests = json.loads(rv.data)

    target_contest = standardized_contests[0]
    opportunistic_contest = standardized_contests[1]
    rv = put_json(
        client,
        f"/api/election/{election_id}/contest",
        [
            {
                "id": str(uuid.uuid4()),
                "name": target_contest["name"],
                "numWinners": 1,
                "jurisdictionIds": target_contest["jurisdictionIds"],
                "isTargeted": True,
            },
            {
                "id": str(uuid.uuid4()),
                "name": opportunistic_contest["name"],
                "numWinners": 1,
                "jurisdictionIds": opportunistic_contest["jurisdictionIds"],
                "isTargeted": False,
            },
        ],
    )
    assert_ok(rv)

    # AA selects a sample size and launches the audit
    rv = client.get(f"/api/election/{election_id}/contest")
    contests = json.loads(rv.data)["contests"]
    target_contest_id = contests[0]["id"]
    opportunistic_contest_id = contests[1]["id"]

    rv = client.get(f"/api/election/{election_id}/sample-sizes/1")
    sample_size_options = json.loads(rv.data)["sampleSizes"]
    assert len(sample_size_options) == 1
    sample_size = sample_size_options[target_contest_id][0]
    snapshot.assert_match(sample_size)

    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {"roundNum": 1, "sampleSizes": {target_contest_id: sample_size}},
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/round",
    )
    round_1_id = json.loads(rv.data)["rounds"][0]["id"]

    # Check jurisdiction status after starting the round
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]
    snapshot.assert_match(jurisdictions[0]["currentRoundStatus"])
    snapshot.assert_match(jurisdictions[1]["currentRoundStatus"])

    # JAs create audit boards
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    for jurisdiction_id in target_contest["jurisdictionIds"]:
        rv = post_json(
            client,
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_1_id}/audit-board",
            [{"name": "Audit Board #1"}],
        )
        assert_ok(rv)

    # Audit boards audit all the ballots.
    # Our goal is to mostly make the audit board interpretations match the CVRs
    # for the target contest, messing up just a couple in order to trigger a
    # second round. For convenience, using the same format as the CVR to
    # specify our audit results.
    # Tabulator, Batch, Ballot, Choice 1-1, Choice 1-2, Choice 2-1, Choice 2-2, Choice 2-3
    # We also specify the expected discrepancies.
    round_1_audit_results_j1 = {
        ("J1", "TABULATOR1", "BATCH1", 1): ("0,1,1,1,0", (None, None)),
        ("J1", "TABULATOR1", "BATCH2", 2): ("0,1,1,1,0", (None, None)),
        ("J1", "TABULATOR1", "BATCH2", 3): ("1,1,0,1,1", (1, 2)),  # CVR: 1,0,1,0,1
        ("J1", "TABULATOR2", "BATCH2", 2): ("1,1,1,1,1", (None, None)),
        ("J1", "TABULATOR2", "BATCH2", 3): ("1,0,,,", (-1, 1)),  # CVR: ,,1,0,1
        ("J1", "TABULATOR2", "BATCH2", 4): ("blank", (None, None)),
        ("J1", "TABULATOR2", "BATCH2", 5): ("not on ballot", (None, 1)),  # CVR: ,,1,0,1
        ("J1", "TABULATOR2", "BATCH2", 6): ("not found", (2, 2)),  # not in CVR
    }

    round_1_audit_results_j2 = {
        ("J2", "TABULATOR1", "BATCH1", 1): ("1,0,1,0,0", (-2, -1)),  # CVR: 0,1,1,1,0
        ("J2", "TABULATOR1", "BATCH1", 3): ("0,1,1,1,0", (None, None)),
        ("J2", "TABULATOR1", "BATCH2", 1): ("1,0,1,0,1", (None, None)),
        ("J2", "TABULATOR2", "BATCH1", 1): ("1,0,1,1,0", (None, None)),
        ("J2", "TABULATOR2", "BATCH2", 1): ("1,0,1,0,1", (None, None)),
        ("J2", "TABULATOR2", "BATCH2", 2): ("1,1,1,1,1", (None, None)),
        ("J2", "TABULATOR2", "BATCH2", 3): (",,1,0,1", (None, None)),
        ("J2", "TABULATOR2", "BATCH2", 5): (",,1,0,1", (None, None)),
        ("J2", "TABULATOR2", "BATCH2", 6): ("1,0,1,0,1", (2, 2)),  # not in CVR
    }
    round_1_audit_results = {**round_1_audit_results_j1, **round_1_audit_results_j2}

    audit_all_ballots(
        round_1_id,
        round_1_audit_results,
        target_contest_id,
        opportunistic_contest_id,
    )

    # Only sign off J1
    audit_boards = AuditBoard.query.filter_by(jurisdiction_id=jurisdiction_ids[0]).all()
    for audit_board in audit_boards:
        audit_board.signed_off_at = datetime.now(timezone.utc)
    db_session.commit()

    # Check jurisdiction status after auditing J1
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]
    assert jurisdictions[0]["currentRoundStatus"]["status"] == "COMPLETE"
    assert jurisdictions[1]["currentRoundStatus"]["status"] == "IN_PROGRESS"
    snapshot.assert_match(jurisdictions[0]["currentRoundStatus"])
    snapshot.assert_match(jurisdictions[1]["currentRoundStatus"])

    # Check discrepancy counts
    rv = client.get(f"/api/election/{election_id}/discrepancy-counts")
    discrepancy_counts = json.loads(rv.data)
    expected_discrepancy_counts = count_discrepancies(round_1_audit_results)
    assert (
        discrepancy_counts[jurisdictions[0]["id"]]
        == expected_discrepancy_counts[jurisdictions[0]["name"]]
    )
    # We rely on the frontend to hide the discrepancy counts for J2 until J2 is
    # signed off to avoid duplicating the round status logic in this endpoint
    assert (
        discrepancy_counts[jurisdictions[1]["id"]]
        == expected_discrepancy_counts[jurisdictions[1]["name"]]
    )

    # Check the discrepancy report - only the first jurisdiction should have
    # audit results so far since the second jurisdiction hasn't signed off yet
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/discrepancy-report")
    discrepancy_report = rv.data.decode("utf-8")
    check_discrepancies(discrepancy_report, round_1_audit_results_j1)
    for row in csv.DictReader(io.StringIO(discrepancy_report)):
        if row["Jurisdiction Name"] == "J2":
            assert row["Audited?"] == "NOT_AUDITED"
            assert row["Audit Result: Contest 1"] == ""
            assert row["CVR Result: Contest 1"] == ""
            assert row["Change in Results: Contest 1"] == ""
            assert row["Change in Margin: Contest 1"] == ""

    # Sign off J2
    audit_boards = AuditBoard.query.filter_by(jurisdiction_id=jurisdiction_ids[1]).all()
    for audit_board in audit_boards:
        audit_board.signed_off_at = datetime.now(timezone.utc)
    db_session.commit()

    # Check jurisdiction status after auditing J2
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]
    assert jurisdictions[0]["currentRoundStatus"]["status"] == "COMPLETE"
    assert jurisdictions[1]["currentRoundStatus"]["status"] == "COMPLETE"
    snapshot.assert_match(jurisdictions[0]["currentRoundStatus"])
    snapshot.assert_match(jurisdictions[1]["currentRoundStatus"])

    # End the round
    rv = client.post(f"/api/election/{election_id}/round/current/finish")
    assert_ok(rv)

    # Check the audit report
    rv = client.get(f"/api/election/{election_id}/report")
    assert_match_report(rv.data, snapshot)
    audit_report = rv.data.decode("utf-8")

    # Check the discrepancy report
    rv = client.get(f"/api/election/{election_id}/discrepancy-report")
    discrepancy_report = rv.data.decode("utf-8")
    assert (
        discrepancy_report
        == audit_report.split("######## SAMPLED BALLOTS ########\r\n")[1]
    )
    check_discrepancies(discrepancy_report, round_1_audit_results)

    # Start a second round
    rv = client.get(f"/api/election/{election_id}/sample-sizes/2")
    sample_size_options = json.loads(rv.data)["sampleSizes"]
    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {
            "roundNum": 2,
            "sampleSizes": {
                contest_id: options[0]
                for contest_id, options in sample_size_options.items()
            },
        },
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/round",
    )
    round_2_id = json.loads(rv.data)["rounds"][1]["id"]

    # Sample sizes endpoint should still return round 1 sample size
    rv = client.get(f"/api/election/{election_id}/sample-sizes/1")
    sample_size_options = json.loads(rv.data)["sampleSizes"]
    assert len(sample_size_options) == 1
    assert sample_size_options[target_contest_id][0] == sample_size

    # JAs create audit boards
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    for jurisdiction_id in target_contest["jurisdictionIds"]:
        rv = post_json(
            client,
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_2_id}/audit-board",
            [{"name": "Audit Board #1"}],
        )
        assert_ok(rv)

    # For round 2, audit results should not have any positive discrepancies so
    # the audit can complete.
    round_2_audit_results = {
        ("J2", "TABULATOR1", "BATCH1", 2): ("1,0,1,0,1", (None, None)),
        ("J2", "TABULATOR1", "BATCH2", 3): ("1,0,1,0,1", (None, None)),
        ("J2", "TABULATOR2", "BATCH2", 4): (",,1,1,0", (None, -1)),
    }

    audit_all_ballots(
        round_2_id, round_2_audit_results, target_contest_id, opportunistic_contest_id
    )
    audit_boards = AuditBoard.query.filter(
        AuditBoard.jurisdiction_id.in_(jurisdiction_ids)
    ).all()
    for audit_board in audit_boards:
        audit_board.signed_off_at = datetime.now(timezone.utc)
    db_session.commit()

    # Check jurisdiction status after auditing
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    jurisdictions = json.loads(rv.data)["jurisdictions"]
    assert jurisdictions[0]["currentRoundStatus"]["status"] == "COMPLETE"
    assert jurisdictions[1]["currentRoundStatus"]["status"] == "COMPLETE"
    snapshot.assert_match(jurisdictions[0]["currentRoundStatus"])
    snapshot.assert_match(jurisdictions[1]["currentRoundStatus"])

    # Check discrepancy counts
    rv = client.get(f"/api/election/{election_id}/discrepancy-counts")
    discrepancy_counts = json.loads(rv.data)
    round_2_sampled_ballot_keys = [
        ballot_key(ballot)
        for ballot in SampledBallot.query.join(SampledBallotDraw)
        .filter_by(round_id=round_2_id)
        .all()
    ]
    expected_discrepancy_counts = count_discrepancies(
        {
            **{
                ballot: result
                for ballot, result in round_1_audit_results.items()
                if ballot in round_2_sampled_ballot_keys
            },
            **round_2_audit_results,
        }
    )
    assert (
        discrepancy_counts[jurisdictions[0]["id"]]
        == expected_discrepancy_counts[jurisdictions[0]["name"]]
    )
    assert (
        discrepancy_counts[jurisdictions[1]["id"]]
        == expected_discrepancy_counts[jurisdictions[1]["name"]]
    )

    # End the round
    rv = client.post(f"/api/election/{election_id}/round/current/finish")
    assert_ok(rv)

    # Check the audit report
    rv = client.get(f"/api/election/{election_id}/report")
    assert_match_report(rv.data, snapshot)
    audit_report = rv.data.decode("utf-8")

    # Check the discrepancy report
    rv = client.get(f"/api/election/{election_id}/discrepancy-report")
    discrepancy_report = rv.data.decode("utf-8")
    assert (
        discrepancy_report
        == audit_report.split("######## SAMPLED BALLOTS ########\r\n")[1]
    )
    check_discrepancies(discrepancy_report, round_2_audit_results)


# This function can be used to generate the correct audit results in case you
# need to update the above test case.
def generate_audit_results(round_id: str):  # pragma: no cover
    ballots_and_cvrs = (
        SampledBallot.query.filter_by(status=BallotStatus.NOT_AUDITED)
        .join(SampledBallotDraw)
        .filter_by(round_id=round_id)
        .join(Batch)
        .join(Jurisdiction)
        .outerjoin(
            CvrBallot,
            and_(
                CvrBallot.batch_id == SampledBallot.batch_id,
                CvrBallot.ballot_position == SampledBallot.ballot_position,
            ),
        )
        .order_by(
            Jurisdiction.name,
            Batch.tabulator,
            Batch.name,
            SampledBallot.ballot_position,
        )
        .with_entities(SampledBallot, CvrBallot)
        .all()
    )

    def ballot_key(ballot: SampledBallot):
        return (
            ballot.batch.jurisdiction.name,
            ballot.batch.tabulator,
            ballot.batch.name,
            ballot.ballot_position,
        )

    print(
        {
            ballot_key(ballot): (cvr.interpretations if cvr else "no cvr", (None, None))
            for ballot, cvr in ballots_and_cvrs
        }
    )


def test_ballot_comparison_cvr_metadata(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    cvrs,  # pylint: disable=unused-argument
    snapshot,
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)

    # AA creates contests
    rv = put_json(
        client,
        f"/api/election/{election_id}/contest",
        [
            {
                "id": str(uuid.uuid4()),
                "name": "Contest 2",
                "numWinners": 1,
                "jurisdictionIds": jurisdiction_ids[:2],
                "isTargeted": True,
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Contest 1",
                "numWinners": 1,
                "jurisdictionIds": jurisdiction_ids[:2],
                "isTargeted": False,
            },
        ],
    )
    assert_ok(rv)

    # AA selects a sample size and launches the audit
    rv = client.get(f"/api/election/{election_id}/contest")
    contests = json.loads(rv.data)["contests"]
    target_contest_id = contests[0]["id"]

    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {
            "roundNum": 1,
            "sampleSizes": {
                target_contest_id: {"key": "custom", "size": 20, "prob": None}
            },
        },
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/round",
    )
    round_1_id = json.loads(rv.data)["rounds"][0]["id"]

    # JA creates audit boards
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
        [
            {"name": "Audit Board #1"},
        ],
    )
    assert_ok(rv)

    # Check that the CVR metadata is included in the ballot retrieval list
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/ballots/retrieval-list"
    )
    retrieval_list = rv.data.decode("utf-8").replace("\r\n", "\n")
    snapshot.assert_match(retrieval_list)

    # Check that the CVR metadata is included with each ballot for JAs/audit boards
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/ballots"
    )
    ballots = json.loads(rv.data)["ballots"]
    assert len(ballots) == len(retrieval_list.splitlines()) - 1

    assert ballots[0]["batch"]["name"] == "BATCH1"
    assert ballots[0]["batch"]["tabulator"] == "TABULATOR1"
    assert ballots[0]["position"] == 1
    assert ballots[0]["imprintedId"] == "1-1-1"

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board"
    )
    audit_board = json.loads(rv.data)["auditBoards"][0]

    set_logged_in_user(client, UserType.AUDIT_BOARD, audit_board["id"])
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board/{audit_board['id']}/ballots"
    )
    ballots = json.loads(rv.data)["ballots"]

    assert ballots[0]["batch"]["name"] == "BATCH1"
    assert ballots[0]["batch"]["tabulator"] == "TABULATOR1"
    assert ballots[0]["position"] == 1
    assert ballots[0]["imprintedId"] == "1-1-1"


def test_ballot_comparison_sample_size_validation(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    cvrs,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    contest_id = str(uuid.uuid4())
    rv = put_json(
        client,
        f"/api/election/{election_id}/contest",
        [
            {
                "id": contest_id,
                "name": "Contest 2",
                "numWinners": 1,
                "jurisdictionIds": jurisdiction_ids[:2],
                "isTargeted": True,
            }
        ],
    )
    assert_ok(rv)

    bad_sample_sizes = [
        (
            {contest_id: {"key": "bad_key", "size": 10, "prob": None}},
            "Invalid sample size key for contest Contest 2: bad_key",
        ),
        (
            {contest_id: {"key": "custom", "size": 3000, "prob": None}},
            "Sample size for contest Contest 2 must be less than or equal to: 30 (the total number of ballots in the contest)",
        ),
        (
            {contest_id: {"key": "custom", "size": 30, "prob": None}},
            "For a full hand tally, use the ballot polling or batch comparison audit type.",
        ),
        (
            {contest_id: {"key": "supersimple", "size": 31, "prob": None}},
            "For a full hand tally, use the ballot polling or batch comparison audit type.",
        ),
    ]
    for bad_sample_size, expected_error in bad_sample_sizes:
        rv = post_json(
            client,
            f"/api/election/{election_id}/round",
            {"roundNum": 1, "sampleSizes": bad_sample_size},
        )
        assert rv.status_code == 400
        assert json.loads(rv.data) == {
            "errors": [
                {
                    "message": expected_error,
                    "errorType": "Bad Request",
                }
            ]
        }


def test_ballot_comparison_multiple_targeted_contests_sample_size(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    cvrs,  # pylint: disable=unused-argument
    snapshot,
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)

    contest_1_id = str(uuid.uuid4())
    contest_2_id = str(uuid.uuid4())
    rv = put_json(
        client,
        f"/api/election/{election_id}/contest",
        [
            {
                "id": contest_1_id,
                "name": "Contest 1",
                "numWinners": 1,
                "jurisdictionIds": jurisdiction_ids[:2],
                "isTargeted": True,
            },
            {
                "id": contest_2_id,
                "name": "Contest 2",
                "numWinners": 1,
                "jurisdictionIds": jurisdiction_ids[:2],
                "isTargeted": True,
            },
        ],
    )
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/sample-sizes/1")
    sample_size_options = json.loads(rv.data)["sampleSizes"]

    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {
            "roundNum": 1,
            "sampleSizes": {
                contest_id: options[0]
                for contest_id, options in sample_size_options.items()
            },
        },
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/round",
    )
    round_1_id = json.loads(rv.data)["rounds"][0]["id"]

    sampled_ballots = (
        SampledBallot.query.filter_by(status=BallotStatus.NOT_AUDITED)
        .join(SampledBallotDraw)
        .filter_by(round_id=round_1_id)
        .join(Batch)
        .order_by(Batch.tabulator, Batch.name, SampledBallot.ballot_position)
        .all()
    )

    contest_1 = Contest.query.get(contest_1_id)
    contest_2 = Contest.query.get(contest_2_id)

    for ballot in sampled_ballots:
        audit_ballot(ballot, contest_1_id, Interpretation.VOTE, [contest_1.choices[0]])
        audit_ballot(ballot, contest_2_id, Interpretation.VOTE, [contest_2.choices[0]])

    rv = client.post(f"/api/election/{election_id}/round/current/finish")
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/sample-sizes/2")
    sample_size_options = json.loads(rv.data)["sampleSizes"]
    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {
            "roundNum": 2,
            "sampleSizes": {
                contest_id: options[0]
                for contest_id, options in sample_size_options.items()
            },
        },
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/round",
    )
    round_2_id = json.loads(rv.data)["rounds"][1]["id"]

    round_2_sample_sizes = list(
        RoundContest.query.filter_by(round_id=round_2_id)
        .join(Contest)
        .order_by(Contest.name)
        .values(RoundContest.sample_size)
    )
    snapshot.assert_match(round_2_sample_sizes)


def test_ballot_comparison_ess(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
    ess_manifests,  # pylint: disable=unused-argument
    snapshot,
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

    # Upload CVRs that have some choice names missing across jurisdictions and
    # enough overvotes/undervotes so that at least a few of each get sampled
    j1_cvr = """Cast Vote Record,Precinct,Ballot Style,Contest 1,Contest 2
1,p,bs,Choice 1-1,Choice 2-1
2,p,bs,Choice 1-2,Choice 2-1
3,p,bs,Choice 1-1,Choice 2-1
4,p,bs,Choice 1-2,Choice 2-1
5,p,bs,undervote,undervote
6,p,bs,Choice 1-2,Choice 2-1
7,p,bs,Choice 1-1,Choice 2-1
8,p,bs,Choice 1-2,Choice 2-1
9,p,bs,undervote,undervote
10,p,bs,undervote,undervote
11,p,bs,Choice 1-1,Choice 2-2
12,p,bs,Choice 1-2,Choice 2-2
13,p,bs,Choice 1-1,Choice 2-2
15,p,bs,Choice 1-2,Choice 2-2
"""
    j2_cvr = """Cast Vote Record,Precinct,Ballot Style,Contest 1,Contest 2
1,p,bs,Choice 1-1,Choice 2-1
2,p,bs,Choice 1-1,Choice 2-1
3,p,bs,Choice 1-1,Choice 2-1
4,p,bs,Choice 1-1,Choice 2-1
5,p,bs,overvote,overvote
6,p,bs,overvote,overvote
7,p,bs,Choice 1-1,Choice 2-1
8,p,bs,Choice 1-1,Choice 2-1
9,p,bs,overvote,overvote
10,p,bs,Choice 1-1,Choice 2-3
11,p,bs,Choice 1-1,Choice 2-3
12,p,bs,Choice 1-1,Choice 2-3
13,p,bs,Choice 1-1,Choice 2-3
15,p,bs,Choice 1-1,Choice 2-3
"""
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs",
        data={
            "cvrs": [
                (
                    io.BytesIO(ESS_BALLOTS_1.encode()),
                    "ess_ballots_1.csv",
                ),
                (
                    io.BytesIO(ESS_BALLOTS_2.encode()),
                    "ess_ballots_2.csv",
                ),
                (
                    io.BytesIO(j1_cvr.encode()),
                    "ess_cvr.csv",
                ),
            ],
            "cvrFileType": "ESS",
        },
    )
    assert_ok(rv)
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/cvrs",
        data={
            "cvrs": [
                (
                    io.BytesIO(ESS_BALLOTS_1.encode()),
                    "ess_ballots_1.csv",
                ),
                (
                    io.BytesIO(ESS_BALLOTS_2.encode()),
                    "ess_ballots_2.csv",
                ),
                (
                    io.BytesIO(j2_cvr.encode()),
                    "ess_cvr.csv",
                ),
            ],
            "cvrFileType": "ESS",
        },
    )
    assert_ok(rv)

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)

    # AA selects contests
    rv = put_json(
        client,
        f"/api/election/{election_id}/contest",
        [
            {
                "id": str(uuid.uuid4()),
                "name": "Contest 1",
                "numWinners": 1,
                "jurisdictionIds": jurisdiction_ids[:2],
                "isTargeted": True,
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Contest 2",
                "numWinners": 1,
                "jurisdictionIds": jurisdiction_ids[:2],
                "isTargeted": False,
            },
        ],
    )
    assert_ok(rv)

    # AA selects a sample size and launches the audit
    rv = client.get(f"/api/election/{election_id}/contest")
    contests = json.loads(rv.data)["contests"]
    target_contest, opportunistic_contest = contests

    # Choices should be unioned across jurisdictions
    compare_json(
        target_contest["choices"],
        [
            {"id": assert_is_id, "name": "Choice 1-1", "numVotes": 16},
            {"id": assert_is_id, "name": "Choice 1-2", "numVotes": 6},
        ],
    )

    rv = client.get(f"/api/election/{election_id}/sample-sizes/1")
    sample_size_options = json.loads(rv.data)["sampleSizes"]
    assert len(sample_size_options) == 1
    sample_size = sample_size_options[target_contest["id"]][0]

    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {"roundNum": 1, "sampleSizes": {target_contest["id"]: sample_size}},
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/round",
    )
    round_1_id = json.loads(rv.data)["rounds"][0]["id"]

    # JAs create audit boards
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    for jurisdiction_id in target_contest["jurisdictionIds"]:
        rv = post_json(
            client,
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_1_id}/audit-board",
            [{"name": "Audit Board #1"}],
        )
        assert_ok(rv)

    # Audit boards audit all the ballots.
    # Tabulator, Batch, Ballot, Choice 1-1, Choice 1-2, Choice 2-1, Choice 2-2, Choice 2-3
    # generate_audit_results(round_1_id)
    audit_results = {
        ("J1", "0001", "BATCH1", 1): ("1,0,1,0,0", (None, None)),
        ("J1", "0001", "BATCH2", 2): ("0,1,1,0,0", (None, None)),
        ("J1", "0001", "BATCH2", 3): ("0,0,0,0,0", (None, None)),  # CVR: u,u,u,u,u
        ("J1", "0002", "BATCH1", 3): ("0,1,1,0,0", (None, None)),
        ("J1", "0002", "BATCH2", 1): ("0,1,0,1,0", (1, 1)),  # CVR: u,u,u,u,u
        ("J1", "0002", "BATCH2", 5): ("0,1,0,1,0", (None, None)),
        ("J2", "0001", "BATCH1", 1): ("1,0,1,0,0", (None, None)),
        ("J2", "0001", "BATCH1", 3): ("1,0,1,0,0", (None, None)),
        ("J2", "0001", "BATCH2", 3): ("1,1,1,0,1", (None, None)),  # CVR: o,o,o,o,o
        ("J2", "0002", "BATCH1", 3): ("0,1,0,1,0", (1, 1)),  # CVR: o,o,o,o,o
        ("J2", "0002", "BATCH2", 1): ("1,0,0,0,1", (None, None)),
        ("J2", "0002", "BATCH2", 2): ("1,0,0,0,1", (None, None)),
        ("J2", "0002", "BATCH2", 5): ("1,0,0,0,1", (None, None)),
    }

    audit_all_ballots(
        round_1_id, audit_results, target_contest["id"], opportunistic_contest["id"]
    )
    audit_boards = AuditBoard.query.filter(
        AuditBoard.jurisdiction_id.in_(jurisdiction_ids)
    ).all()
    for audit_board in audit_boards:
        audit_board.signed_off_at = datetime.now(timezone.utc)
    db_session.commit()

    # End the round
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.post(f"/api/election/{election_id}/round/current/finish")
    assert_ok(rv)

    # Check the audit report
    rv = client.get(f"/api/election/{election_id}/report")
    assert_match_report(rv.data, snapshot)
    audit_report = rv.data.decode("utf-8")

    # Check the discrepancy report
    rv = client.get(f"/api/election/{election_id}/discrepancy-report")
    discrepancy_report = rv.data.decode("utf-8")
    assert (
        discrepancy_report
        == audit_report.split("######## SAMPLED BALLOTS ########\r\n")[1]
    )
    check_discrepancies(discrepancy_report, audit_results)


def test_ballot_comparison_sample_preview(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    manifests,  # pylint: disable=unused-argument
    cvrs,  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
    snapshot,
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)

    contest_id = str(uuid.uuid4())
    rv = put_json(
        client,
        f"/api/election/{election_id}/contest",
        [
            {
                "id": contest_id,
                "name": "Contest 1",
                "numWinners": 1,
                "jurisdictionIds": jurisdiction_ids[:2],
                "isTargeted": True,
            }
        ],
    )
    assert_ok(rv)

    # Start computing a sample preview
    rv = client.get(f"/api/election/{election_id}/sample-sizes/1")
    sample_size_options = json.loads(rv.data)["sampleSizes"]
    sample_size = sample_size_options[contest_id][0]
    rv = post_json(
        client,
        f"/api/election/{election_id}/sample-preview",
        {"sampleSizes": {contest_id: sample_size}},
    )
    assert_ok(rv)

    # Check the computed sample preview
    rv = client.get(f"/api/election/{election_id}/sample-preview")
    assert rv.status_code == 200
    sample_preview = json.loads(rv.data)
    compare_json(
        sample_preview["task"],
        {
            "status": "PROCESSED",
            "startedAt": assert_is_date,
            "completedAt": assert_is_date,
            "error": None,
        },
    )
    assert len(sample_preview["jurisdictions"]) == len(jurisdiction_ids)
    snapshot.assert_match(sample_preview["jurisdictions"])

    # Make sure it matches the sample drawn when we start a round
    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {"roundNum": 1, "sampleSizes": {contest_id: sample_size}},
    )
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    assert rv.status_code == 200
    jurisdictions = json.loads(rv.data)["jurisdictions"]

    for i, jurisdiction in enumerate(jurisdictions):
        preview = sample_preview["jurisdictions"][i]
        assert preview["name"] == jurisdiction["name"]
        assert preview["numSamples"] == jurisdiction["currentRoundStatus"]["numSamples"]
        assert preview["numUnique"] == jurisdiction["currentRoundStatus"]["numUnique"]
