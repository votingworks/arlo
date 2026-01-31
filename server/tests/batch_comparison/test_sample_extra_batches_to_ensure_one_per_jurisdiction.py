import pytest
from flask.testing import FlaskClient

from ...database import db_session
from ...models import *
from ..helpers import *


@pytest.fixture
def org_id(client: FlaskClient, request) -> str:
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
            b"Batch Name,Number of Ballots\nBatch 01,500\nBatch 02,250\nBatch 03,250\n"
        ),
        election_id,
        jurisdiction_ids[1],
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
    batch_tallies_file = (
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
    )
    rv = upload_batch_tallies(
        client,
        io.BytesIO(batch_tallies_file),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)
    batch_tallies_file = (
        b"Batch Name,candidate 1,candidate 2,candidate 3\n"
        b"Batch 01,500,250,250\n"
        b"Batch 02,300,100,100\n"
        b"Batch 03,200,150,150\n"
    )
    rv = upload_batch_tallies(
        client,
        io.BytesIO(batch_tallies_file),
        election_id,
        jurisdiction_ids[1],
    )
    assert_ok(rv)


BASE_SAMPLE_ORG = "TEST-ORG/base-sample"
EXTRA_SAMPLE_ORG = "TEST-ORG/sample-extra-batches-to-ensure-one-per-jurisdiction"


@pytest.mark.parametrize(
    "org_id",
    [
        BASE_SAMPLE_ORG,
        EXTRA_SAMPLE_ORG,
    ],
    indirect=True,
)
def test_sample_extra_batches_to_ensure_one_per_jurisdiction(
    client: FlaskClient,
    org_id: str,
    election_id: str,
    jurisdiction_ids: list[str],
    round_1_id,
    snapshot,
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches"
    )
    assert rv.status_code == 200
    j1_batches = json.loads(rv.data)["batches"]

    expected_base_sample = [
        "Batch 01",
        "Batch 02",
        "Batch 04",
        "Batch 06",
        "Batch 08",
        "Batch 12",
    ]
    expected_extra_sample = []

    if org_id == BASE_SAMPLE_ORG:
        assert {batch["name"] for batch in j1_batches} == set(expected_base_sample)
    else:
        assert {batch["name"] for batch in j1_batches} == set(
            expected_base_sample + expected_extra_sample
        )

    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[1]}/round/{round_1_id}/batches"
    )
    assert rv.status_code == 200
    j2_batches = json.loads(rv.data)["batches"]

    # Nothing is selected from jurisdiction 2 by default, but when the relevant flag is enabled, we
    # add a batch from jurisdiction 2 to ensure at least one batch is sampled from each
    # jurisdiction.
    expected_base_sample = []
    expected_extra_sample = ["Batch 02"]

    if org_id == BASE_SAMPLE_ORG:
        assert {batch["name"] for batch in j2_batches} == set(expected_base_sample)
    else:
        assert {batch["name"] for batch in j2_batches} == set(
            expected_base_sample + expected_extra_sample
        )
