import io
import json
import csv
from flask.testing import FlaskClient

from ...models import *  # pylint: disable=wildcard-import
from ..helpers import *  # pylint: disable=wildcard-import
from ...worker.bgcompute import (
    bgcompute_update_standardized_contests_file,
    bgcompute_update_cvr_file,
    bgcompute_update_ballot_manifest_file,
)
from .conftest import TEST_CVRS


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
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
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

    # Contest metadata isn't set when creating contest if no manifest/CVRs
    contest = Contest.query.get(contest_id)
    assert contest.total_ballots_cast is None
    assert contest.votes_allowed is None
    assert contest.choices == []

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
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
    bgcompute_update_ballot_manifest_file(election_id)

    # Contest total ballots isn't set when only some manifests uploaded
    contest = Contest.query.get(contest_id)
    assert contest.total_ballots_cast is None
    assert contest.votes_allowed is None
    assert contest.choices == []

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
    bgcompute_update_ballot_manifest_file(election_id)

    # Contest total ballots is set when all manifests uploaded
    contest = Contest.query.get(contest_id)
    assert contest.total_ballots_cast == 30
    assert contest.votes_allowed is None
    assert contest.choices == []

    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs",
        data={"cvrs": (io.BytesIO(TEST_CVRS.encode()), "cvrs.csv",)},
    )
    assert_ok(rv)
    bgcompute_update_cvr_file(election_id)

    # Contest votes allowed/choices isn't set when only some CVRs uploaded
    contest = Contest.query.get(contest_id)
    assert contest.total_ballots_cast == 30  # Set from manifest
    assert contest.votes_allowed is None
    assert contest.choices == []

    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/cvrs",
        data={"cvrs": (io.BytesIO(TEST_CVRS.encode()), "cvrs.csv",)},
    )
    assert_ok(rv)
    bgcompute_update_cvr_file(election_id)

    # Contest votes allowed/choices is set when all CVRs uploaded
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

    # Contest metadata changes on new manifest/CVR upload
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
    bgcompute_update_ballot_manifest_file(election_id)

    new_cvr = "\n".join(TEST_CVRS.splitlines()[:10])
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs",
        data={"cvrs": (io.BytesIO(new_cvr.encode()), "cvrs.csv",)},
    )
    assert_ok(rv)
    bgcompute_update_cvr_file(election_id)

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
    rv = client.get(f"/api/election/{election_id}/sample-sizes")
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
    rv = client.get(f"/api/election/{election_id}/sample-sizes")
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

    rv = client.get(f"/api/election/{election_id}/sample-sizes")
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


def audit_all_ballots(
    round_id: str, audit_results, target_contest_id, opportunistic_contest_id
):
    choice_1_1, choice_1_2 = Contest.query.get(target_contest_id).choices
    choice_2_1, choice_2_2, choice_2_3 = Contest.query.get(
        opportunistic_contest_id
    ).choices

    def ballot_key(ballot: SampledBallot):
        return (
            ballot.batch.jurisdiction.name,
            ballot.batch.tabulator,
            ballot.batch.name,
            ballot.ballot_position,
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

    for ballot in sampled_ballots:
        interpretation_str, _ = audit_results[ballot_key(ballot)]

        if interpretation_str == "not found":
            ballot.status = BallotStatus.NOT_FOUND
            continue

        ballot.status = BallotStatus.AUDITED

        if interpretation_str == "blank":
            audit_ballot(ballot, target_contest_id, Interpretation.BLANK)
            audit_ballot(ballot, opportunistic_contest_id, Interpretation.BLANK)

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
                    Interpretation.VOTE
                    if vote_choice_1_1 != ""
                    else Interpretation.CONTEST_NOT_ON_BALLOT
                ),
                target_choices,
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
                    Interpretation.VOTE
                    if vote_choice_2_1 != ""
                    else Interpretation.CONTEST_NOT_ON_BALLOT
                ),
                opportunistic_choices,
            )

    end_round(round.election, round)
    db_session.commit()


# Check expected discrepancies against audit report
def check_discrepancies(report_data, audit_results):
    report = report_data.decode("utf-8")
    report_ballots = list(
        csv.DictReader(
            io.StringIO(report.split("######## SAMPLED BALLOTS ########\r\n")[1])
        )
    )
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
        parse_discrepancy = lambda d: int(d) if d != "" else None
        assert expected_discrepancies == (
            parse_discrepancy(row["Discrepancy: Contest 1"]),
            parse_discrepancy(row["Discrepancy: Contest 2"]),
        )


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

    bgcompute_update_standardized_contests_file(election_id)

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

    rv = client.get(f"/api/election/{election_id}/sample-sizes")
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

    rv = client.get(f"/api/election/{election_id}/round",)
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
    audit_results = {
        ("J1", "TABULATOR1", "BATCH1", 1): ("0,1,1,1,0", (None, None)),
        ("J1", "TABULATOR1", "BATCH1", 2): ("1,0,1,0,1", (None, None)),
        ("J1", "TABULATOR1", "BATCH2", 2): ("0,1,1,1,0", (None, None)),
        ("J1", "TABULATOR1", "BATCH2", 3): ("1,1,0,1,1", (1, 2)),  # CVR: 1,0,1,0,1
        ("J1", "TABULATOR2", "BATCH1", 2): ("1,0,1,0,1", (None, None)),
        ("J1", "TABULATOR2", "BATCH2", 1): ("1,0,1,0,1", (None, None)),
        ("J1", "TABULATOR2", "BATCH2", 2): ("1,1,1,1,1", (None, None)),
        ("J1", "TABULATOR2", "BATCH2", 3): ("blank", (None, 1)),  # CVR: ,,1,0,1
        ("J1", "TABULATOR2", "BATCH2", 4): (",,1,1,0", (None, None)),
        ("J1", "TABULATOR2", "BATCH2", 5): (",,1,0,1", (None, None)),
        ("J1", "TABULATOR2", "BATCH2", 6): ("not found", (2, 2)),  # not in CVR
        ("J2", "TABULATOR1", "BATCH1", 1): ("1,0,1,0,0", (-2, -1)),  # CVR: 0,1,1,1,0
        ("J2", "TABULATOR1", "BATCH1", 2): ("1,0,1,0,1", (None, None)),
        ("J2", "TABULATOR1", "BATCH1", 3): ("0,1,1,1,0", (None, None)),
        ("J2", "TABULATOR1", "BATCH2", 1): ("not found", (2, 2)),  # CVR: 1,0,1,0,1
        ("J2", "TABULATOR1", "BATCH2", 3): ("1,0,1,0,1", (None, None)),
        ("J2", "TABULATOR2", "BATCH1", 1): ("0,1,1,1,0", (None, None)),
        ("J2", "TABULATOR2", "BATCH1", 2): ("1,0,1,0,1", (None, None)),
        ("J2", "TABULATOR2", "BATCH2", 1): (",,,,", (1, 1)),  # CVR :1,0,1,0,1
        ("J2", "TABULATOR2", "BATCH2", 2): ("1,1,1,1,1", (None, None)),
        ("J2", "TABULATOR2", "BATCH2", 3): (",,1,0,1", (None, None)),
        ("J2", "TABULATOR2", "BATCH2", 4): (",,1,1,0", (None, None)),
        ("J2", "TABULATOR2", "BATCH2", 5): (",,1,0,1", (None, None)),
        ("J2", "TABULATOR2", "BATCH2", 6): ("1,0,1,0,1", (2, 2)),  # not in CVR
    }

    audit_all_ballots(
        round_1_id, audit_results, target_contest_id, opportunistic_contest_id
    )

    # Check the audit report
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/report")
    assert_match_report(rv.data, snapshot)

    check_discrepancies(rv.data, audit_results)

    # Start a second round
    rv = post_json(client, f"/api/election/{election_id}/round", {"roundNum": 2},)
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/round",)
    round_2_id = json.loads(rv.data)["rounds"][1]["id"]

    # Sample sizes endpoint should still return round 1 sample size
    rv = client.get(f"/api/election/{election_id}/sample-sizes")
    sample_size_options = json.loads(rv.data)["sampleSizes"]
    assert len(sample_size_options) == 1
    assert sample_size_options[target_contest_id][0] == sample_size

    # For round 2, audit results should match the CVR exactly.
    audit_results = {
        ("J1", "TABULATOR1", "BATCH2", 1): ("1,0,1,0,1", (None, None)),
        ("J1", "TABULATOR2", "BATCH1", 1): ("0,1,1,1,0", (None, None)),
        ("J2", "TABULATOR1", "BATCH2", 2): ("0,1,1,1,0", (None, None)),
        ("J2", "TABULATOR2", "BATCH1", 3): ("1,0,1,1,0", (None, None)),
    }

    audit_all_ballots(
        round_2_id, audit_results, target_contest_id, opportunistic_contest_id
    )

    rv = client.get(f"/api/election/{election_id}/report")
    assert_match_report(rv.data, snapshot)
    check_discrepancies(rv.data, audit_results)


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

    rv = client.get(f"/api/election/{election_id}/round",)
    round_1_id = json.loads(rv.data)["rounds"][0]["id"]

    # JA creates audit boards
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
        [{"name": "Audit Board #1"},],
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
    ]
    for bad_sample_size, expected_error in bad_sample_sizes:
        rv = post_json(
            client,
            f"/api/election/{election_id}/round",
            {"roundNum": 1, "sampleSizes": bad_sample_size},
        )
        assert rv.status_code == 400
        assert json.loads(rv.data) == {
            "errors": [{"message": expected_error, "errorType": "Bad Request",}]
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

    rv = client.get(f"/api/election/{election_id}/sample-sizes")
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

    rv = client.get(f"/api/election/{election_id}/round",)
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

    round = Round.query.get(round_1_id)
    end_round(round.election, round)
    db_session.commit()

    rv = post_json(client, f"/api/election/{election_id}/round", {"roundNum": 2})
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/round",)
    round_2_id = json.loads(rv.data)["rounds"][1]["id"]

    round_2_sample_sizes = list(
        RoundContest.query.filter_by(round_id=round_2_id).values(
            RoundContest.sample_size
        )
    )
    snapshot.assert_match(round_2_sample_sizes)


def test_ballot_comparison_cvr_choice_names_dont_match(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
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
                "name": "Contest 1",
                "numWinners": 1,
                "jurisdictionIds": jurisdiction_ids[:2],
                "isTargeted": True,
            },
        ],
    )
    assert_ok(rv)

    # Change the CVR contest choice name
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs",
        data={
            "cvrs": (
                io.BytesIO(TEST_CVRS.replace("Choice 1-1", "Choice A").encode()),
                "cvrs.csv",
            )
        },
    )
    assert_ok(rv)
    bgcompute_update_cvr_file(election_id)

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/sample-sizes")
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
                "error": (
                    "CVR choice names don't match for contest Contest 1:\n"
                    "J2: Choice 1-1, Choice 1-2\n"
                    "J1: Choice 1-2, Choice A"
                ),
            },
        },
    )
