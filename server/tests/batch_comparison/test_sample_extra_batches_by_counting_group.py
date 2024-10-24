import pytest
from flask.testing import FlaskClient

from ...database import db_session
from ...models import *  # pylint: disable=wildcard-import
from ..helpers import *  # pylint: disable=wildcard-import


@pytest.fixture
def org_id(client: FlaskClient, request) -> str:  # pylint: disable=unused-argument
    # Allow specifying a custom test org via @pytest.mark.parametrize to toggle relevant feature
    # flags
    org_id = str(request.param)
    org = Organization.query.get(org_id)
    if not org:
        org = Organization(id=org_id, name=org_id)
        db_session.add(org)
        add_admin_to_org(org_id, DEFAULT_AA_EMAIL)
        db_session.commit()
    return org_id


@pytest.fixture
def manifests(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
):
    # Upload manifests with counting group in the Container column
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest",
        data={
            "manifest": (
                # Mostly HMPB counting groups
                io.BytesIO(
                    b"Container,Batch Name,Number of Ballots\n"
                    b"Absentee by Mail,Batch 1,500\n"
                    b"Absentee by Mail,Batch 2,500\n"
                    b"Absentee by Mail,Batch 3,500\n"
                    b"Absentee by Mail,Batch 4,500\n"
                    b"Provisional,Batch 5,100\n"
                    b"Provisional,Batch 6,100\n"
                    b"Provisional,Batch 7,100\n"
                    b"Provisional,Batch 8,100\n"
                    b"Election Day,Batch 9,100\n"
                ),
                "manifest.csv",
            )
        },
    )
    assert_ok(rv)
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/ballot-manifest",
        data={
            "manifest": (
                # Mostly BMD counting groups
                io.BytesIO(
                    b"Container,Batch Name,Number of Ballots\n"
                    b"Election Day,Batch 1,500\n"
                    b"Elections Day,Batch 2,500\n"
                    b"Advance Voting,Batch 3,500\n"
                    b"Advanced Voting,Batch 4,500\n"
                    b"Advanced Voting,Batch 5,250\n"
                    b"Provisional,Batch 6,250\n"
                ),
                "manifest.csv",
            )
        },
    )
    assert_ok(rv)


@pytest.fixture
def batch_tallies(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    manifests,  # pylint: disable=unused-argument
):
    # Upload batch tallies
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    batch_tallies_file = (
        b"Batch Name,candidate 1,candidate 2,candidate 3\n"
        b"Batch 1,500,250,250\n"
        b"Batch 2,500,250,250\n"
        b"Batch 3,500,250,250\n"
        b"Batch 4,500,250,250\n"
        b"Batch 5,100,50,50\n"
        b"Batch 6,100,50,50\n"
        b"Batch 7,100,50,50\n"
        b"Batch 8,100,50,50\n"
        b"Batch 9,100,50,50\n"
    )
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/batch-tallies",
        data={
            "batchTallies": (
                io.BytesIO(batch_tallies_file),
                "batchTallies.csv",
            )
        },
    )
    batch_tallies_file = (
        b"Batch Name,candidate 1,candidate 2,candidate 3\n"
        b"Batch 1,500,250,250\n"
        b"Batch 2,500,250,250\n"
        b"Batch 3,500,250,250\n"
        b"Batch 4,500,250,250\n"
        b"Batch 5,100,50,50\n"
        b"Batch 6,100,50,50\n"
    )
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/batch-tallies",
        data={
            "batchTallies": (
                io.BytesIO(batch_tallies_file),
                "batchTallies.csv",
            )
        },
    )
    assert_ok(rv)


@pytest.mark.parametrize(
    "org_id",
    [
        "TEST-ORG/sample-extra-batches-by-counting-group/automatically-end-audit-after-one-round",
        "TEST-ORG/sample-extra-batches-by-counting-group",
    ],
    indirect=True,
)
def test_sample_extra_batches_by_counting_group(
    client: FlaskClient,
    org_id: str,
    election_id: str,
    jurisdiction_ids: List[str],
    round_1_id,
    snapshot,
):
    # Check that some extra batches were sampled
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches"
    )
    assert rv.status_code == 200
    j1_batches = json.loads(rv.data)["batches"]
    # Generated by turning off the feature flag
    expected_regular_sampled_batch_names = ["Batch 1", "Batch 3", "Batch 6", "Batch 8"]
    # The only HMPB batch in J1
    expected_extra_sampled_batch_names = ["Batch 9"]
    assert {batch["name"] for batch in j1_batches} == set(
        expected_regular_sampled_batch_names + expected_extra_sampled_batch_names
    )

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_1_id}/batches"
    )
    assert rv.status_code == 200
    j2_batches = json.loads(rv.data)["batches"]
    # Generated by turning off the feature flag
    expected_regular_sampled_batch_names = ["Batch 3"]
    # The only BMD batch in J2
    expected_extra_sampled_batch_names = ["Batch 6"]
    assert {batch["name"] for batch in j2_batches} == set(
        expected_regular_sampled_batch_names + expected_extra_sampled_batch_names
    )

    # Record some batch results
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/contest")
    assert rv.status_code == 200
    contests = json.loads(rv.data)["contests"]
    choice_ids = [choice["id"] for choice in contests[0]["choices"]]

    batch_results = {
        j1_batches[0]["id"]: {
            choice_ids[0]: 400,
            choice_ids[1]: 50,
            choice_ids[2]: 40,
        },
        j1_batches[1]["id"]: {
            choice_ids[0]: 400,
            choice_ids[1]: 50,
            choice_ids[2]: 40,
        },
        j1_batches[2]["id"]: {
            choice_ids[0]: 100,
            choice_ids[1]: 50,
            choice_ids[2]: 40,
        },
        j1_batches[3]["id"]: {
            choice_ids[0]: 100,
            choice_ids[1]: 50,
            choice_ids[2]: 40,
        },
        # The extra batch
        j1_batches[4]["id"]: {
            choice_ids[0]: 0,
            choice_ids[1]: 0,
            choice_ids[2]: 0,
        },
    }

    for batch_id, results in batch_results.items():
        set_logged_in_user(
            client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
        )
        rv = put_json(
            client,
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/{batch_id}/results",
            [{"name": "Tally Sheet #1", "results": results}],
        )
        assert_ok(rv)

    # Finalize the results
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/finalize",
    )
    assert_ok(rv)

    # Now do the second jurisdiction
    batch_results = {
        j2_batches[0]["id"]: {
            choice_ids[0]: 100,
            choice_ids[1]: 100,
            choice_ids[2]: 40,
        },
        # The extra batch
        j2_batches[1]["id"]: {
            choice_ids[0]: 1,
            choice_ids[1]: 200,
            choice_ids[2]: 200,
        },
    }

    for batch_id, results in batch_results.items():
        set_logged_in_user(
            client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
        )
        rv = put_json(
            client,
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_1_id}/batches/{batch_id}/results",
            [{"name": "Tally Sheet #1", "results": results}],
        )
        assert_ok(rv)

    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_1_id}/batches/finalize",
    )
    assert_ok(rv)

    # End the round
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.post(f"/api/election/{election_id}/round/current/finish")
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/round")
    is_audit_complete = json.loads(rv.data)["rounds"][0]["isAuditComplete"]

    if (
        org_id
        == "TEST-ORG/sample-extra-batches-by-counting-group/automatically-end-audit-after-one-round"
    ):
        assert is_audit_complete

        # Check the audit report
        rv = client.get(f"/api/election/{election_id}/report")
        assert_match_report(rv.data, snapshot)

        # The audit results should be the same as the audit results without the
        # extra sampled batches
        report = scrub_datetime(rv.data.decode("utf-8"))
        # Generated by turning off the feature flag
        expected_audit_results_line = "1,Contest 1,Targeted,7,No,0.1225641097,DATETIME,DATETIME,candidate 1: 1100; candidate 2: 300; candidate 3: 200"
        assert expected_audit_results_line in report

    elif org_id == "TEST-ORG/sample-extra-batches-by-counting-group":
        assert not is_audit_complete

    else:
        raise Exception(f"Invalid org ID {org_id}")


@pytest.mark.parametrize(
    "org_id",
    [
        "TEST-ORG/sample-extra-batches-by-counting-group/automatically-end-audit-after-one-round"
    ],
    indirect=True,
)
def test_sample_extra_batches_with_no_extra_batches_to_sample(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_id: str,
    batch_tallies,  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
):
    # Upload manifests that only have one type of batch (BMD/HMPB) per jurisdiction
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest",
        data={
            "manifest": (
                # Only HMPB counting groups
                io.BytesIO(
                    b"Container,Batch Name,Number of Ballots\n"
                    b"Absentee by Mail,Batch 1,500\n"
                    b"Absentee by Mail,Batch 2,500\n"
                    b"Absentee by Mail,Batch 3,500\n"
                    b"Absentee by Mail,Batch 4,500\n"
                    b"Provisional,Batch 5,100\n"
                    b"Provisional,Batch 6,100\n"
                    b"Provisional,Batch 7,100\n"
                    b"Provisional,Batch 8,100\n"
                    b"Provisional,Batch 9,100\n"
                ),
                "manifest.csv",
            )
        },
    )
    assert_ok(rv)
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/ballot-manifest",
        data={
            "manifest": (
                # Only BMD counting groups
                io.BytesIO(
                    b"Container,Batch Name,Number of Ballots\n"
                    b"Election Day,Batch 1,500\n"
                    b"Election Day,Batch 2,500\n"
                    b"Advanced Voting,Batch 3,500\n"
                    b"Advanced Voting,Batch 4,500\n"
                    b"Advanced Voting,Batch 5,250\n"
                    b"Advanced Voting,Batch 6,250\n"
                ),
                "manifest.csv",
            )
        },
    )
    assert_ok(rv)

    # Start the audit
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/sample-sizes/1")
    assert rv.status_code == 200
    sample_size_options = json.loads(rv.data)["sampleSizes"]
    sample_size = sample_size_options[contest_id][0]

    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {"roundNum": 1, "sampleSizes": {contest_id: sample_size}},
    )
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/round")
    rounds = json.loads(rv.data)["rounds"]
    round_1_id = rounds[0]["id"]

    # Check that no extra batches were sampled, since there weren't extra
    # batches of the appropriate type to sample
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches"
    )
    assert rv.status_code == 200
    j1_batches = json.loads(rv.data)["batches"]
    expected_regular_sampled_batch_names = ["Batch 1", "Batch 3", "Batch 6", "Batch 8"]
    assert {batch["name"] for batch in j1_batches} == set(
        expected_regular_sampled_batch_names
    )

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_1_id}/batches"
    )
    assert rv.status_code == 200
    j2_batches = json.loads(rv.data)["batches"]
    expected_regular_sampled_batch_names = ["Batch 3"]
    assert {batch["name"] for batch in j2_batches} == set(
        expected_regular_sampled_batch_names
    )


@pytest.mark.parametrize(
    "org_id",
    [
        "TEST-ORG/sample-extra-batches-by-counting-group/automatically-end-audit-after-one-round"
    ],
    indirect=True,
)
def test_sample_extra_batches_min_percentage_of_jurisdiction_ballots_selected(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_id: str,
    batch_tallies,  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest",
        data={
            "manifest": (
                io.BytesIO(
                    b"Container,Batch Name,Number of Ballots\n"
                    b"Absentee by Mail,Batch 1,500\n"  # HMPB group
                    b"Election Day,Batch 2,500\n"
                    b"Election Day,Batch 3,500\n"
                    b"Election Day,Batch 4,500\n"
                    b"Election Day,Batch 5,100\n"
                    b"Election Day,Batch 6,100\n"
                    b"Election Day,Batch 7,100\n"
                    b"Election Day,Batch 8,100\n"
                    b"Election Day,Batch 9,1000000\n"  # Must be selected to hit the 2% selection threshold
                ),
                "manifest.csv",
            )
        },
    )
    assert_ok(rv)

    # Start the audit
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/sample-sizes/1")
    assert rv.status_code == 200

    custom_zero_sample_size = {"key": "custom", "size": 0, "prob": None}
    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {"roundNum": 1, "sampleSizes": {contest_id: custom_zero_sample_size}},
    )
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/round")
    rounds = json.loads(rv.data)["rounds"]
    round1_id = rounds[0]["id"]

    # Check that the relevant batches were selected
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round1_id}/batches"
    )

    assert rv.status_code == 200
    j1_batches = json.loads(rv.data)["batches"]
    j1_batch_names = {batch["name"] for batch in j1_batches}
    assert len(j1_batch_names) >= 2
    assert "Batch 1" in j1_batch_names  # HMPB group
    assert (
        "Batch 9" in j1_batch_names
    )  # Must be selected to hit the 2% selection threshold.
    # Also satisfies the BMD group expectation so we test that explicitly in another test.


@pytest.mark.parametrize(
    "org_id",
    [
        "TEST-ORG/sample-extra-batches-by-counting-group/automatically-end-audit-after-one-round"
    ],
    indirect=True,
)
def test_sample_extra_batches_hmpb_and_bmd_groups_selected(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_id: str,
    batch_tallies,  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest",
        data={
            "manifest": (
                io.BytesIO(
                    b"Container,Batch Name,Number of Ballots\n"
                    b"Absentee by Mail,Batch 1,500\n"  # HMPB group
                    b"Absentee by Mail,Batch 2,500\n"
                    b"Election Day,Batch 3,500\n"  # BMD group
                    b"Election Day,Batch 4,500\n"
                    b"Election Day,Batch 5,100\n"
                    b"Election Day,Batch 6,100\n"
                    b"Election Day,Batch 7,100\n"
                    b"Election Day,Batch 8,100\n"
                    b"Election Day,Batch 9,100\n"
                ),
                "manifest.csv",
            )
        },
    )
    assert_ok(rv)

    # Start the audit
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/sample-sizes/1")
    assert rv.status_code == 200

    custom_zero_sample_size = {"key": "custom", "size": 0, "prob": None}
    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {"roundNum": 1, "sampleSizes": {contest_id: custom_zero_sample_size}},
    )
    assert_ok(rv)

    rv = client.get(f"/api/election/{election_id}/round")
    rounds = json.loads(rv.data)["rounds"]
    round1_id = rounds[0]["id"]

    # Check that the relevant batches were selected
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round1_id}/batches"
    )
    assert rv.status_code == 200
    j1_batches = json.loads(rv.data)["batches"]
    j1_batch_names = {batch["name"] for batch in j1_batches}
    assert len(j1_batch_names) == 2

    hmpb_batch_names = ["Batch 1", "Batch 2"]
    bmd_batch_names = [
        "Batch 3",
        "Batch 4",
        "Batch 5",
        "Batch 6",
        "Batch 7",
        "Batch 8",
        "Batch 9",
    ]

    hmpb_batch_found = False
    bmd_batch_found = False

    batch_names = j1_batch_names.copy()
    while len(batch_names) > 0:
        batch_name = batch_names.pop()
        if batch_name in hmpb_batch_names:
            hmpb_batch_found = True
        if batch_name in bmd_batch_names:
            bmd_batch_found = True

    assert (
        hmpb_batch_found
    ), f"Expected to find one HMPB batch. HMPB batches: {hmpb_batch_names}. Actual batches: {j1_batch_names}"
    assert (
        bmd_batch_found
    ), f"Expected to find one BMD batch. BMD batches: {bmd_batch_names}. Actual batches: {j1_batch_names}"


@pytest.mark.parametrize(
    "org_id",
    [
        "TEST-ORG/sample-extra-batches-by-counting-group",
    ],
    indirect=True,
)
def test_sample_extra_batches_with_invalid_counting_group(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_id: str,  # pylint: disable=unused-argument
    batch_tallies,  # pylint: disable=unused-argument
    election_settings,  # pylint: disable=unused-argument
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.put(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest",
        data={
            "manifest": (
                io.BytesIO(
                    b"Container,Batch Name,Number of Ballots\n"
                    b"Invalid Counting Group,Batch 1,500\n"
                ),
                "manifest.csv",
            )
        },
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/ballot-manifest"
    )
    compare_json(
        json.loads(rv.data),
        {
            "file": {
                "name": "manifest.csv",
                "uploadedAt": assert_is_date,
            },
            "processing": {
                "status": ProcessingStatus.ERRORED,
                "startedAt": assert_is_date,
                "completedAt": assert_is_date,
                "error": 'Invalid value for column "Container", row 2: "Invalid Counting Group". Use the Batch Audit File Preparation Tool to create your ballot manifest, or correct this value to one of the following: Advanced Voting, Advance Voting, Election Day, Elections Day, Absentee by Mail, Provisional.',
            },
        },
    )
