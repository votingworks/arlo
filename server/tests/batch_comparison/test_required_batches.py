import pytest
from flask.testing import FlaskClient

from ...models import *
from ..helpers import *


@pytest.fixture
def org_id(client: FlaskClient, request) -> str:
    org_id = str(request.param)
    org = Organization.query.get(org_id)
    if not org:
        create_org(org_id)
    return org_id


@pytest.fixture
def contest_ids(client: FlaskClient, election_id: str, jurisdiction_ids: list[str]):
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    contests = [
        {
            "id": str(uuid.uuid4()),
            "name": "Contest 1",
            "isTargeted": True,
            "choices": [
                {"id": str(uuid.uuid4()), "name": "candidate 1", "numVotes": 4600},
                {"id": str(uuid.uuid4()), "name": "candidate 2", "numVotes": 2300},
                {"id": str(uuid.uuid4()), "name": "candidate 3", "numVotes": 2300},
            ],
            "numWinners": 1,
            "votesAllowed": 2,
            "jurisdictionIds": jurisdiction_ids,
        },
    ]
    rv = put_json(client, f"/api/election/{election_id}/contest", contests)
    assert_ok(rv)
    return [str(contest["id"]) for contest in contests]


# The root conftest assigns a different admin to J3 than J1/J2
def j3_email(election_id: str) -> str:
    return f"j3-{election_id}@example.com"


def set_logged_in_ja(client: FlaskClient, election_id: str, jurisdiction_index: int):
    email = (
        j3_email(election_id)
        if jurisdiction_index == 2
        else default_ja_email(election_id)
    )
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, email)


@pytest.fixture
def manifests(client: FlaskClient, election_id: str, jurisdiction_ids: list[str]):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = upload_ballot_manifest(
        client,
        io.BytesIO(
            b"Batch Name,Number of Ballots\n"
            b"Batch 01,500\n"
            b"Batch 02,500\n"
            b"Batch 03,500\n"
            b"Batch 04,500\n"
            b"Batch 05,100\n"
            b"Batch 06,100\n"
            b"Batch 07,100\n"
            b"Batch 08,100\n"
            b"Batch 09,100\n"
            b"Batch 10,500\n"
            b"Batch 11,500\n"
            b"Batch 12,500\n"
        ),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)
    rv = upload_ballot_manifest(
        client,
        io.BytesIO(
            b"Batch Name,Number of Ballots\nBatch 01,100\nBatch 02,100\nBatch 03,100\n"
        ),
        election_id,
        jurisdiction_ids[1],
    )
    assert_ok(rv)
    set_logged_in_user(client, UserType.JURISDICTION_ADMIN, j3_email(election_id))
    rv = upload_ballot_manifest(
        client,
        io.BytesIO(
            b"Batch Name,Number of Ballots\nBatch 01,100\nBatch 02,100\nBatch 03,100\n"
        ),
        election_id,
        jurisdiction_ids[2],
    )
    assert_ok(rv)


@pytest.fixture
def batch_tallies(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
    contest_ids: list[str],
    manifests,
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = upload_batch_tallies(
        client,
        io.BytesIO(
            b"Batch Name,candidate 1,candidate 2,candidate 3\n"
            b"Batch 01,500,250,250\n"
            b"Batch 02,500,250,250\n"
            b"Batch 03,500,250,250\n"
            b"Batch 04,500,250,250\n"
            b"Batch 05,100,50,50\n"
            b"Batch 06,100,50,50\n"
            b"Batch 07,100,50,50\n"
            b"Batch 08,100,50,50\n"
            b"Batch 09,100,50,50\n"
            b"Batch 10,500,250,250\n"
            b"Batch 11,500,250,250\n"
            b"Batch 12,500,250,250\n"
        ),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)
    for jurisdiction_index, jurisdiction_id in list(enumerate(jurisdiction_ids))[1:]:
        set_logged_in_ja(client, election_id, jurisdiction_index)
        rv = upload_batch_tallies(
            client,
            io.BytesIO(
                b"Batch Name,candidate 1,candidate 2,candidate 3\n"
                b"Batch 01,100,50,50\n"
                b"Batch 02,100,50,50\n"
                b"Batch 03,100,50,50\n"
            ),
            election_id,
            jurisdiction_id,
        )
        assert_ok(rv)


# This org also has sample-extra-batches-to-ensure-one-per-jurisdiction
# enabled, mirroring Maryland's setup
REQUIRED_BATCHES_ORG = "TEST-ORG/required-batches"


def batch_id_by_name(jurisdiction_id: str, name: str) -> str:
    return Batch.query.filter_by(jurisdiction_id=jurisdiction_id, name=name).one().id


def start_round_1(client: FlaskClient, election_id: str) -> str:
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/sample-sizes/1")
    assert rv.status_code == 200
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
    rv = client.get(f"/api/election/{election_id}/round")
    return json.loads(rv.data)["rounds"][0]["id"]


def get_sampled_batches(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
    round_id: str,
    jurisdiction_index: int,
):
    set_logged_in_ja(client, election_id, jurisdiction_index)
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[jurisdiction_index]}/round/{round_id}/batches"
    )
    assert rv.status_code == 200
    return json.loads(rv.data)["batches"]


def extra_ticket_numbers(batch_id: str) -> list[str]:
    return [
        draw.ticket_number
        for draw in SampledBatchDraw.query.filter_by(batch_id=batch_id)
        if draw.ticket_number == EXTRA_TICKET_NUMBER
    ]


@pytest.mark.parametrize("org_id", [REQUIRED_BATCHES_ORG], indirect=True)
def test_required_batches(
    client: FlaskClient,
    org_id: str,
    election_id: str,
    jurisdiction_ids: list[str],
    contest_ids: list[str],
    election_settings,
    batch_tallies,
    snapshot,
):
    # Before launching the audit, a support user marks batches as required in
    # J1 and J2, not J3
    set_support_user(client, DEFAULT_SUPPORT_EMAIL)
    rv = put_json(
        client,
        f"/api/support/jurisdictions/{jurisdiction_ids[0]}/required-batches",
        {
            "batchIds": [
                batch_id_by_name(jurisdiction_ids[0], "Batch 01"),
                batch_id_by_name(jurisdiction_ids[0], "Batch 05"),
            ]
        },
    )
    assert_ok(rv)
    rv = put_json(
        client,
        f"/api/support/jurisdictions/{jurisdiction_ids[1]}/required-batches",
        {"batchIds": [batch_id_by_name(jurisdiction_ids[1], "Batch 02")]},
    )
    assert_ok(rv)

    rv = client.get(f"/api/support/jurisdictions/{jurisdiction_ids[0]}/batches")
    assert {
        batch["name"]: batch["required"]
        for batch in json.loads(rv.data)["batches"]
        if batch["required"]
    } == {"Batch 01": True, "Batch 05": True}

    # Start the audit
    round_1_id = start_round_1(client, election_id)

    # In J1, the required Batch 01 was randomly sampled, so it shouldn't get an
    # extra draw. The required Batch 05 wasn't, so it should be added as an
    # extra batch.
    j1_batches = get_sampled_batches(
        client, election_id, jurisdiction_ids, round_1_id, 0
    )
    expected_random_sample = [
        "Batch 01",
        "Batch 03",
        "Batch 04",
        "Batch 07",
        "Batch 11",
    ]
    assert {batch["name"] for batch in j1_batches} == set(
        expected_random_sample + ["Batch 05"]
    )
    assert extra_ticket_numbers(batch_id_by_name(jurisdiction_ids[0], "Batch 01")) == []
    assert extra_ticket_numbers(batch_id_by_name(jurisdiction_ids[0], "Batch 05")) == [
        EXTRA_TICKET_NUMBER
    ]

    # In J2, nothing was randomly sampled, so the required Batch 02 should be
    # added as an extra batch. It also counts as J2's one batch per
    # jurisdiction, so no additional batch should be selected.
    j2_batches = get_sampled_batches(
        client, election_id, jurisdiction_ids, round_1_id, 1
    )
    assert {batch["name"] for batch in j2_batches} == {"Batch 02"}
    assert extra_ticket_numbers(batch_id_by_name(jurisdiction_ids[1], "Batch 02")) == [
        EXTRA_TICKET_NUMBER
    ]

    # In J3, nothing was randomly sampled and there are no required batches, so
    # one batch should be selected to ensure one batch per jurisdiction.
    j3_batches = get_sampled_batches(
        client, election_id, jurisdiction_ids, round_1_id, 2
    )
    assert {batch["name"] for batch in j3_batches} == {"Batch 02"}
    assert extra_ticket_numbers(batch_id_by_name(jurisdiction_ids[2], "Batch 02")) == [
        EXTRA_TICKET_NUMBER
    ]

    # Audit all sampled batches with results matching the reported tallies
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/contest")
    contest = json.loads(rv.data)["contests"][0]
    choice_ids = [choice["id"] for choice in contest["choices"]]

    for jurisdiction_index, jurisdiction_id in enumerate(jurisdiction_ids):
        reported_tallies = Jurisdiction.query.get(jurisdiction_id).batch_tallies
        for batch in get_sampled_batches(
            client, election_id, jurisdiction_ids, round_1_id, jurisdiction_index
        ):
            results = {
                choice_id: reported_tallies[batch["name"]][contest_ids[0]][choice_id]
                for choice_id in choice_ids
            }
            rv = put_json(
                client,
                f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_1_id}/batches/{batch['id']}/results",
                [{"name": "Tally Sheet #1", "results": results}],
            )
            assert_ok(rv)
        rv = post_json(
            client,
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_1_id}/batches/finalize",
        )
        assert_ok(rv)

    # End the round
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.post(f"/api/election/{election_id}/round/current/finish")
    assert_ok(rv)
    rv = client.get(f"/api/election/{election_id}/round")
    assert json.loads(rv.data)["rounds"][0]["isAuditComplete"]

    # Check that the report shows required batches as Precinct Audit Batches
    rv = client.get(f"/api/election/{election_id}/report")
    assert_match_report(rv.data, snapshot)
    report_rows = scrub_datetime(rv.data.decode("utf-8")).splitlines()
    batch_rows = [
        row
        for row in report_rows
        if row.startswith("J1,") or row.startswith("J2,") or row.startswith("J3,")
    ]
    assert len(batch_rows) == len(expected_random_sample) + 3
    for row in batch_rows:
        jurisdiction_name, batch_name = row.split(",")[:2]
        is_required = (jurisdiction_name, batch_name) in [
            ("J1", "Batch 01"),
            ("J1", "Batch 05"),
            ("J2", "Batch 02"),
        ]
        assert row.endswith(",Yes") == is_required


@pytest.mark.parametrize("org_id", [REQUIRED_BATCHES_ORG], indirect=True)
def test_required_batches_validation(
    client: FlaskClient,
    org_id: str,
    election_id: str,
    jurisdiction_ids: list[str],
    contest_ids: list[str],
    election_settings,
    batch_tallies,
):
    def put_required_batches(jurisdiction_id, batch_ids):
        return put_json(
            client,
            f"/api/support/jurisdictions/{jurisdiction_id}/required-batches",
            {"batchIds": batch_ids},
        )

    def assert_conflict(rv, expected_message):
        assert rv.status_code == 409
        assert json.loads(rv.data)["errors"][0]["message"] == expected_message

    set_support_user(client, DEFAULT_SUPPORT_EMAIL)

    # Invalid jurisdiction
    rv = put_required_batches("not-a-real-jurisdiction", [])
    assert rv.status_code == 404

    # Invalid JSON
    rv = put_json(
        client,
        f"/api/support/jurisdictions/{jurisdiction_ids[0]}/required-batches",
        {},
    )
    assert rv.status_code == 400

    # Batches from another jurisdiction
    rv = put_required_batches(
        jurisdiction_ids[0], [batch_id_by_name(jurisdiction_ids[1], "Batch 01")]
    )
    assert rv.status_code == 400
    assert json.loads(rv.data)["errors"][0]["message"] == "Invalid batch ids"

    # Non-batch-comparison audit
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    ballot_polling_election_id = create_election(
        client,
        audit_name="Test Audit test_required_batches_validation ballot polling",
        organization_id=org_id,
    )
    rv = upload_jurisdictions_file(
        client,
        io.BytesIO(
            f"Jurisdiction,Admin Email\nJ1,{default_ja_email(ballot_polling_election_id)}\n".encode()
        ),
        ballot_polling_election_id,
    )
    assert_ok(rv)
    ballot_polling_jurisdiction_id = (
        Jurisdiction.query.filter_by(election_id=ballot_polling_election_id).one().id
    )
    set_support_user(client, DEFAULT_SUPPORT_EMAIL)
    rv = put_required_batches(ballot_polling_jurisdiction_id, [])
    assert_conflict(
        rv, "Required batches are only supported for batch comparison audits"
    )

    # Batch comparison audit in an org without the feature flag enabled
    no_flag_org_id = "TEST-ORG/required-batches-not-enabled"
    if not Organization.query.get(no_flag_org_id):
        create_org(no_flag_org_id)
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    no_flag_election_id = create_election(
        client,
        audit_name="Test Audit test_required_batches_validation flag disabled",
        audit_type=AuditType.BATCH_COMPARISON,
        audit_math_type=AuditMathType.MACRO,
        organization_id=no_flag_org_id,
    )
    rv = upload_jurisdictions_file(
        client,
        io.BytesIO(
            f"Jurisdiction,Admin Email\nJ1,{default_ja_email(no_flag_election_id)}\n".encode()
        ),
        no_flag_election_id,
    )
    assert_ok(rv)
    no_flag_jurisdiction_id = (
        Jurisdiction.query.filter_by(election_id=no_flag_election_id).one().id
    )
    set_support_user(client, DEFAULT_SUPPORT_EMAIL)
    rv = put_required_batches(no_flag_jurisdiction_id, [])
    assert_conflict(rv, "Required batches are not enabled for this organization")

    # After the audit has launched
    start_round_1(client, election_id)
    set_support_user(client, DEFAULT_SUPPORT_EMAIL)
    rv = put_required_batches(
        jurisdiction_ids[0], [batch_id_by_name(jurisdiction_ids[0], "Batch 01")]
    )
    assert_conflict(
        rv, "Batches cannot be marked as required after the audit has launched"
    )


@pytest.mark.parametrize("org_id", [REQUIRED_BATCHES_ORG], indirect=True)
def test_required_batches_with_combined_batches(
    client: FlaskClient,
    org_id: str,
    election_id: str,
    jurisdiction_ids: list[str],
    contest_ids: list[str],
    election_settings,
    batch_tallies,
    snapshot,
):
    # J1's Batch 05 won't be randomly sampled, so it will be added as an extra
    # batch
    set_support_user(client, DEFAULT_SUPPORT_EMAIL)
    rv = put_json(
        client,
        f"/api/support/jurisdictions/{jurisdiction_ids[0]}/required-batches",
        {"batchIds": [batch_id_by_name(jurisdiction_ids[0], "Batch 05")]},
    )
    assert_ok(rv)

    # Start the audit
    round_1_id = start_round_1(client, election_id)
    assert extra_ticket_numbers(batch_id_by_name(jurisdiction_ids[0], "Batch 05")) == [
        EXTRA_TICKET_NUMBER
    ]

    # Combine the required extra batch with a sampled batch
    set_support_user(client, DEFAULT_SUPPORT_EMAIL)
    combined_batch_name = "Combined Batch 1"
    combined_sub_batch_names = ["Batch 04", "Batch 05"]
    rv = post_json(
        client,
        f"/api/support/jurisdictions/{jurisdiction_ids[0]}/combined-batches",
        {
            "name": combined_batch_name,
            "subBatchIds": [
                batch_id_by_name(jurisdiction_ids[0], name)
                for name in combined_sub_batch_names
            ],
        },
    )
    assert_ok(rv)

    # Before J1 finalizes results, the report hides its discrepancy columns but
    # should still label required batches
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/report")
    assert rv.status_code == 200
    report_rows = scrub_datetime(rv.data.decode("utf-8")).splitlines()
    combined_row = next(
        row for row in report_rows if row.startswith(f"J1,{combined_batch_name},")
    )
    assert combined_row.endswith(",Yes (Batch 05)")
    batch_01_row = next(row for row in report_rows if row.startswith("J1,Batch 01,"))
    assert batch_01_row.endswith(",")

    # Audit all sampled batches with results matching the reported tallies
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/contest")
    contest = json.loads(rv.data)["contests"][0]
    choice_ids = [choice["id"] for choice in contest["choices"]]

    for jurisdiction_index, jurisdiction_id in enumerate(jurisdiction_ids):
        reported_tallies = Jurisdiction.query.get(jurisdiction_id).batch_tallies
        for batch in get_sampled_batches(
            client, election_id, jurisdiction_ids, round_1_id, jurisdiction_index
        ):
            batch_names = (
                combined_sub_batch_names
                if batch["name"] == combined_batch_name
                else [batch["name"]]
            )
            results = {
                choice_id: sum(
                    reported_tallies[name][contest_ids[0]][choice_id]
                    for name in batch_names
                )
                for choice_id in choice_ids
            }
            rv = put_json(
                client,
                f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_1_id}/batches/{batch['id']}/results",
                [{"name": "Tally Sheet #1", "results": results}],
            )
            assert_ok(rv)
        rv = post_json(
            client,
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_1_id}/batches/finalize",
        )
        assert_ok(rv)

    # End the round
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.post(f"/api/election/{election_id}/round/current/finish")
    assert_ok(rv)

    # The final report should label the combined batch with its required sub
    # batch
    rv = client.get(f"/api/election/{election_id}/report")
    assert_match_report(rv.data, snapshot)
    report_rows = scrub_datetime(rv.data.decode("utf-8")).splitlines()
    combined_row = next(
        row for row in report_rows if row.startswith(f"J1,{combined_batch_name},")
    )
    assert combined_row.endswith(",Yes (Batch 05)")
