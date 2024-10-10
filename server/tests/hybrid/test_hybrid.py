import json
import io
from ...models import *  # pylint: disable=wildcard-import
from ..helpers import *  # pylint: disable=wildcard-import
from ..ballot_comparison.test_ballot_comparison import (
    audit_all_ballots,
    check_discrepancies,
)
from .conftest import TEST_CVRS


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
                "numVotes": 12 + 18,  # CVR + non-CVR
                "numVotesCvr": None,
                "numVotesNonCvr": None,
            },
            {
                "id": assert_is_id,
                "name": "Choice 1-2",
                "numVotes": 8 + 2,
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
                "numVotes": 13 + 7,
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
                "numVotes": 7 + 3,
                "numVotesCvr": None,
                "numVotesNonCvr": None,
            },
        ],
    )

    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    assert rv.status_code == 200
    jurisdictions = json.loads(rv.data)["jurisdictions"]
    assert jurisdictions[0]["cvrs"]["numBallots"] is None


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
                "numVotes": 14 + 16,  # CVR + non-CVR
                "numVotesCvr": 14,
                "numVotesNonCvr": 16,
            },
            {
                "id": assert_is_id,
                "name": "Choice 1-2",
                "numVotes": 6 + 4,
                "numVotesCvr": 6,
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
                "numVotes": 12 + 8,
                "numVotesCvr": 12,
                "numVotesNonCvr": 8,
            },
            {
                "id": assert_is_id,
                "name": "Choice 2-2",
                "numVotes": 5 + 3,
                "numVotesCvr": 5,
                "numVotesNonCvr": 3,
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

    rv = client.get(f"/api/election/{election_id}/jurisdiction")
    assert rv.status_code == 200
    jurisdictions = json.loads(rv.data)["jurisdictions"]
    assert jurisdictions[0]["cvrs"]["numBallots"] == len(TEST_CVRS.splitlines()) - 4


def test_hybrid_sample_size(
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
    rv = client.get(f"/api/election/{election_id}/sample-sizes/1")
    sample_sizes = json.loads(rv.data)["sampleSizes"]
    assert len(sample_sizes) == 1
    snapshot.assert_match(sample_sizes[contest_ids[0]])

    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {
            "roundNum": 1,
            "sampleSizes": {
                contest_id: sample_sizes[0]
                for contest_id, sample_sizes in sample_sizes.items()
            },
        },
    )
    assert_ok(rv)

    # Sample sizes endpoint should still return round 1 options after audit launch
    rv = client.get(f"/api/election/{election_id}/sample-sizes/1")
    assert json.loads(rv.data)["sampleSizes"] == sample_sizes


def test_sample_size_before_manifest(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    contest_ids: List[str],  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
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


def test_sample_size_before_cvrs(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    contest_ids: List[str],  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
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
                {
                    "id": str(uuid.uuid4()),
                    "name": "Bad Choice Name",
                    "numVotes": 1,
                },
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
                "error": (
                    "CVR choice names don't match for contest Contest 1:\n"
                    "J1: Choice 1-1, Choice 1-2\n"
                    "Contest settings: Another Bad Choice Name, Bad Choice Name, Choice 1-2"
                ),
            },
        },
    )


def test_hybrid_two_rounds(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    contest_ids: List[str],  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    cvrs,  # pylint: disable=unused-argument
    snapshot,
):
    # AA selects a sample size and launches the audit
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/sample-sizes/1")
    sample_sizes = json.loads(rv.data)["sampleSizes"]

    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {
            "roundNum": 1,
            "sampleSizes": {
                contest_id: sample_sizes[0]
                for contest_id, sample_sizes in sample_sizes.items()
            },
        },
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/round",
    )
    round_1_id = json.loads(rv.data)["rounds"][0]["id"]

    # Two separate samples (cvr/non-cvr) should have been drawn
    ballot_draws = list(
        SampledBallotDraw.query.join(SampledBallot)
        .join(Batch)
        .join(Jurisdiction)
        .filter_by(election_id=election_id)
        .all()
    )
    sample_size = list(sample_sizes.values())[0][0]
    assert (
        len([draw for draw in ballot_draws if draw.sampled_ballot.batch.has_cvrs])
        == sample_size["sizeCvr"]
    )
    assert (
        len([draw for draw in ballot_draws if not draw.sampled_ballot.batch.has_cvrs])
        == sample_size["sizeNonCvr"]
    )

    # The non-CVR ballots should be sampled without replacement
    assert len(
        {
            draw.ballot_id
            for draw in ballot_draws
            if not draw.sampled_ballot.batch.has_cvrs
        }
    ) == len([draw for draw in ballot_draws if not draw.sampled_ballot.batch.has_cvrs])

    # Check that we're sampling ballots from the two jurisdictions that uploaded manifests
    sampled_jurisdictions = {
        draw.sampled_ballot.batch.jurisdiction_id for draw in ballot_draws
    }
    assert sorted(sampled_jurisdictions) == sorted(jurisdiction_ids[:2])

    # JAs create audit boards
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    for jurisdiction_id in jurisdiction_ids[:2]:
        rv = post_json(
            client,
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_1_id}/audit-board",
            [{"name": "Audit Board #1"}],
        )
        assert_ok(rv)

    # Check that the imprinted ID is included in the ballot retrieval list for CVR ballots
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/ballots/retrieval-list"
    )
    retrieval_list = rv.data.decode("utf-8").replace("\r\n", "\n")
    snapshot.assert_match(retrieval_list)

    # Check that the imprinted ID is included with each CVR ballot for JAs/audit boards
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

    # Audit boards audit all the ballots.
    # Our goal is to mostly make the audit board interpretations match the CVRs
    # for the target contest, messing up just a couple in order to trigger a
    # second round. For convenience, using the same format as the CVR to
    # specify our audit results.
    # Tabulator, Batch, Ballot, Choice 1-1, Choice 1-2, Choice 2-1, Choice 2-2, Choice 2-3
    # We also specify the expected discrepancies.
    audit_results = {
        # CVR ballots
        # We create fake audit results for them based on the CVR
        ("J1", "TABULATOR1", "BATCH1", 1): ("0,1,1,1,0", (None, None)),
        ("J1", "TABULATOR1", "BATCH2", 2): ("1,1,0,1,0", (-1, 1)),  # CVR: 0,1,1,1,0
        ("J1", "TABULATOR1", "BATCH2", 3): ("1,0,1,0,1", (None, None)),
        ("J1", "TABULATOR2", "BATCH2", 2): ("1,1,1,1,1", (None, None)),
        ("J1", "TABULATOR2", "BATCH2", 3): (",,1,0,1", (None, None)),
        ("J1", "TABULATOR2", "BATCH2", 4): ("blank", (None, None)),
        ("J2", "TABULATOR1", "BATCH1", 3): ("0,1,1,1,0", (None, None)),
        ("J2", "TABULATOR1", "BATCH2", 1): ("1,1,1,0,1", (1, None)),
        ("J2", "TABULATOR2", "BATCH1", 1): ("1,0,1,1,0", (None, None)),
        ("J2", "TABULATOR2", "BATCH2", 1): ("1,0,1,0,1", (None, None)),
        ("J2", "TABULATOR2", "BATCH2", 2): ("1,1,1,1,1", (None, None)),
        ("J2", "TABULATOR2", "BATCH2", 3): (",,1,0,1", (None, None)),
        # Non-CVR ballots
        # We create fake audit results for them based on the reported margin,
        # like in ballot polling
        ("J1", "TABULATOR3", "BATCH1", 1): ("1,0,1,0,0", (None, None)),
        ("J1", "TABULATOR3", "BATCH1", 2): ("1,0,1,0,0", (None, None)),
        ("J1", "TABULATOR3", "BATCH1", 3): ("1,0,1,0,0", (None, None)),
        ("J1", "TABULATOR3", "BATCH1", 5): ("1,0,1,0,0", (None, None)),
        ("J1", "TABULATOR3", "BATCH1", 9): ("1,0,1,0,0", (None, None)),
        ("J1", "TABULATOR3", "BATCH1", 10): ("1,0,0,1,0", (None, None)),
        ("J2", "TABULATOR3", "BATCH1", 1): ("1,0,,,", (None, None)),
        ("J2", "TABULATOR3", "BATCH1", 5): ("0,1,,,", (None, None)),
        ("J2", "TABULATOR3", "BATCH1", 10): ("0,1,,,", (None, None)),
    }

    target_contest_id, opportunistic_contest_id = contest_ids

    audit_all_ballots(
        round_1_id, audit_results, target_contest_id, opportunistic_contest_id
    )

    audit_boards = AuditBoard.query.filter_by(round_id=round_1_id).all()
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
    ballots_section = audit_report.split("######## SAMPLED BALLOTS ########\r\n")[1]
    check_discrepancies(ballots_section, audit_results)

    # Get round two sample size
    rv = client.get(f"/api/election/{election_id}/sample-sizes/2")
    round_2_sample_sizes = json.loads(rv.data)["sampleSizes"]
    assert len(round_2_sample_sizes) == 1
    snapshot.assert_match(round_2_sample_sizes[contest_ids[0]])

    # Try to start a second round
    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {
            "roundNum": 2,
            "sampleSizes": {
                contest_id: options[0]
                for contest_id, options in round_2_sample_sizes.items()
            },
        },
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/round",
    )
    round_2 = json.loads(rv.data)["rounds"][1]
    assert round_2["drawSampleTask"]["status"] == "PROCESSED"


def test_hybrid_manifest_validation_too_many_votes(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    election_settings,  # pylint: disable=unused-argument
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    for jurisdiction_id in jurisdiction_ids[:2]:
        rv = client.put(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/ballot-manifest",
            data={
                "manifest": (
                    io.BytesIO(
                        b"Tabulator,Batch Name,Number of Ballots,CVR\n"
                        b"TABULATOR1,BATCH1,3,Y\n"
                        b"TABULATOR1,BATCH2,3,Y\n"
                        b"TABULATOR2,BATCH1,3,Y\n"
                        b"TABULATOR2,BATCH2,6,Y\n"
                        b"TABULATOR3,BATCH1,10,N"
                    ),
                    "manifest.csv",
                )
            },
        )
        assert_ok(rv)

        rv = client.put(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/cvrs",
            data={
                "cvrs": (
                    io.BytesIO(TEST_CVRS.encode()),
                    "cvrs.csv",
                ),
                "cvrFileType": "DOMINION",
            },
        )
        assert_ok(rv)

    # Vote counts that are too large for the total ballots in the manifests
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    contests = [
        {
            "id": str(uuid.uuid4()),
            "name": "Contest 1",
            "isTargeted": True,
            "choices": [
                {"id": str(uuid.uuid4()), "name": "Choice 1-1", "numVotes": 60},
                {"id": str(uuid.uuid4()), "name": "Choice 1-2", "numVotes": 70},
            ],
            "numWinners": 1,
            "votesAllowed": 2,
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
                "error": "Contest Contest 1 vote counts add up to 130 votes, which is more than the total number of ballots across all jurisdiction manifests (50 ballots) times the number of votes allowed (2 votes)",
            },
        },
    )


def test_hybrid_manifest_validation_too_few_cvr_ballots(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    election_settings,  # pylint: disable=unused-argument
):
    contests = [
        {
            "id": str(uuid.uuid4()),
            "name": "Contest 1",
            "isTargeted": True,
            "choices": [
                {"id": str(uuid.uuid4()), "name": "Choice 1-1", "numVotes": 60},
                {"id": str(uuid.uuid4()), "name": "Choice 1-2", "numVotes": 40},
            ],
            "numWinners": 1,
            "votesAllowed": 2,
            "jurisdictionIds": jurisdiction_ids[:2],
        },
    ]
    rv = put_json(client, f"/api/election/{election_id}/contest", contests)
    assert_ok(rv)

    # Too few CVR ballots in the manifest
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    for jurisdiction_id in jurisdiction_ids[:2]:
        rv = client.put(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/ballot-manifest",
            data={
                "manifest": (
                    io.BytesIO(
                        b"Tabulator,Batch Name,Number of Ballots,CVR\n"
                        b"TABULATOR1,BATCH1,3,Y\n"
                        b"TABULATOR1,BATCH2,3,Y\n"
                        b"TABULATOR2,BATCH1,3,Y\n"
                        b"TABULATOR2,BATCH2,4,Y\n"
                        b"TABULATOR3,BATCH1,12,N"
                    ),
                    "manifest.csv",
                )
            },
        )
        assert_ok(rv)

        rv = client.put(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/cvrs",
            data={
                "cvrs": (
                    io.BytesIO(TEST_CVRS.encode()),
                    "cvrs.csv",
                ),
                "cvrFileType": "DOMINION",
            },
        )
        assert_ok(rv)

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
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
                "error": "For contest Contest 1, found 28 ballots in the CVRs, which is more than the total number of CVR ballots across all jurisdiction manifests (26) for jurisdictions in this contest's universe",
            },
        },
    )


def test_hybrid_manifest_validation_few_non_cvr_ballots(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    election_settings,  # pylint: disable=unused-argument
):
    contests = [
        {
            "id": str(uuid.uuid4()),
            "name": "Contest 1",
            "isTargeted": True,
            "choices": [
                {"id": str(uuid.uuid4()), "name": "Choice 1-1", "numVotes": 60},
                {"id": str(uuid.uuid4()), "name": "Choice 1-2", "numVotes": 40},
            ],
            "numWinners": 1,
            "votesAllowed": 2,
            "jurisdictionIds": jurisdiction_ids[:2],
        },
    ]
    rv = put_json(client, f"/api/election/{election_id}/contest", contests)
    assert_ok(rv)

    # Too few non-CVR ballots in the manifest
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    for jurisdiction_id in jurisdiction_ids[:2]:
        rv = client.put(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/ballot-manifest",
            data={
                "manifest": (
                    io.BytesIO(
                        b"Tabulator,Batch Name,Number of Ballots,CVR\n"
                        b"TABULATOR1,BATCH1,3,Y\n"
                        b"TABULATOR1,BATCH2,3,Y\n"
                        b"TABULATOR2,BATCH1,3,Y\n"
                        b"TABULATOR2,BATCH2,6,Y\n"
                        b"TABULATOR3,BATCH1,10,N"
                    ),
                    "manifest.csv",
                )
            },
        )
        assert_ok(rv)

        rv = client.put(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/cvrs",
            data={
                "cvrs": (
                    io.BytesIO(TEST_CVRS.encode()),
                    "cvrs.csv",
                ),
                "cvrFileType": "DOMINION",
            },
        )
        assert_ok(rv)

    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
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
                "error": "For contest Contest 1, choice votes for non-CVR ballots add up to 80 votes, which is more than the total number of non-CVR ballots across all jurisdiction manifests (20 ballots) for jurisdictions in this contest's universe times the number of votes allowed (2 votes)",
            },
        },
    )


def test_hybrid_manifest_validation_too_many_cvr_votes(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
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
                {"id": str(uuid.uuid4()), "name": "Choice 1-1", "numVotes": 13},
                {"id": str(uuid.uuid4()), "name": "Choice 1-2", "numVotes": 10},
            ],
            "numWinners": 1,
            "votesAllowed": 2,
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
                "error": "For contest Contest 1, the CVRs contain more votes for choice Choice 1-1 (14 votes) than were entered in the contest settings (13 votes).",
            },
        },
    )


def test_hybrid_filter_cvrs(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    contest_ids: List[str],  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    cvrs,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/contest")
    contests = json.loads(rv.data)["contests"]

    assert (
        CvrBallot.query.join(Batch)
        .filter_by(has_cvrs=False)
        .join(Jurisdiction)
        .filter_by(election_id=election_id)
        .count()
        == 0
    )

    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    # Add some non-CVR ballots to the CVR
    cvr = TEST_CVRS + (
        "15,TABULATOR3,BATCH1,1,3-1-1,12345,COUNTY,0,1,1,1,0\n"
        "16,TABULATOR3,BATCH1,2,3-1-2,12345,COUNTY,0,1,1,1,0\n"
        "17,TABULATOR3,BATCH1,3,3-1-3,12345,COUNTY,0,1,1,1,0\n"
    )
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/cvrs",
        data={
            "cvrs": (
                io.BytesIO(cvr.encode()),
                "cvrs.csv",
            ),
            "cvrFileType": "DOMINION",
        },
    )
    assert_ok(rv)

    # Contest metadata should be the same, meaning those extra ballots got
    # filtered out
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/contest")
    new_contests = json.loads(rv.data)["contests"]
    assert new_contests == contests

    assert (
        CvrBallot.query.join(Batch)
        .filter_by(has_cvrs=False)
        .join(Jurisdiction)
        .filter_by(election_id=election_id)
        .count()
        == 0
    )


def test_hybrid_custom_sample_size(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    contest_ids: List[str],  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    cvrs,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    sample_size = {
        "key": "custom",
        "size": 10,
        "sizeCvr": 2,
        "sizeNonCvr": 8,
        "prob": None,
    }
    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {
            "roundNum": 1,
            "sampleSizes": {contest_ids[0]: sample_size},
        },
    )
    assert_ok(rv)

    ballot_draws = list(
        SampledBallotDraw.query.join(SampledBallot)
        .join(Batch)
        .join(Jurisdiction)
        .filter_by(election_id=election_id)
        .all()
    )
    assert (
        len([draw for draw in ballot_draws if draw.sampled_ballot.batch.has_cvrs])
        == sample_size["sizeCvr"]
    )
    assert (
        len([draw for draw in ballot_draws if not draw.sampled_ballot.batch.has_cvrs])
        == sample_size["sizeNonCvr"]
    )


def test_hybrid_invalid_sample_size(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],  # pylint: disable=unused-argument
    contest_ids: List[str],  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    cvrs,  # pylint: disable=unused-argument
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    invalid_sample_sizes = [
        (
            {"key": "custom", "prob": None},
            "'sizeCvr' is a required property",
        ),
        (
            {"key": "custom", "sizeCvr": 2, "prob": None},
            "'sizeNonCvr' is a required property",
        ),
        (
            {"key": "custom", "sizeCvr": 2, "sizeNonCvr": 2, "prob": None},
            "'size' is a required property",
        ),
        (
            {
                "key": "custom",
                "size": 50,
                "sizeCvr": 40,
                "sizeNonCvr": 10,
                "prob": None,
            },
            "CVR sample size for contest Contest 1 must be less than or equal to: 30 (the total number of CVR ballots in the contest)",
        ),
        (
            {
                "key": "custom",
                "size": 50,
                "sizeCvr": 20,
                "sizeNonCvr": 30,
                "prob": None,
            },
            "Non-CVR sample size for contest Contest 1 must be less than or equal to: 20 (the total number of non-CVR ballots in the contest)",
        ),
        (
            {
                "key": "custom",
                "size": 50,
                "sizeCvr": 30,
                "sizeNonCvr": 20,
                "prob": None,
            },
            "For a full hand tally, use the ballot polling or batch comparison audit type.",
        ),
        (
            {
                "key": "suite",
                "size": 52,
                "sizeCvr": 31,
                "sizeNonCvr": 21,
                "prob": None,
            },
            "For a full hand tally, use the ballot polling or batch comparison audit type.",
        ),
    ]
    for invalid_sample_size, expected_error in invalid_sample_sizes:
        rv = post_json(
            client,
            f"/api/election/{election_id}/round",
            {
                "roundNum": 1,
                "sampleSizes": {contest_ids[0]: invalid_sample_size},
            },
        )
        assert rv.status_code == 400
        assert json.loads(rv.data) == {
            "errors": [{"errorType": "Bad Request", "message": expected_error}]
        }


def test_hybrid_sample_preview(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: List[str],
    manifests,  # pylint: disable=unused-argument
    cvrs,  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
    snapshot,
):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)

    # Start computing a sample preview
    rv = client.get(f"/api/election/{election_id}/sample-sizes/1")
    sample_size_options = json.loads(rv.data)["sampleSizes"]
    sample_size = sample_size_options[contest_ids[0]][0]
    rv = post_json(
        client,
        f"/api/election/{election_id}/sample-preview",
        {"sampleSizes": {contest_ids[0]: sample_size}},
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
        {"roundNum": 1, "sampleSizes": {contest_ids[0]: sample_size}},
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
