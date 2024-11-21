from typing import List
import io
import pytest
from flask.testing import FlaskClient

from ...models import *  # pylint: disable=wildcard-import
from ..helpers import *  # pylint: disable=wildcard-import
from .test_batch_comparison import check_discrepancies


@pytest.fixture
def jurisdiction_ids(client: FlaskClient, election_id: str) -> List[str]:
    rv = upload_jurisdictions_file(
        client,
        io.BytesIO(
            (
                "Jurisdiction,Admin Email\n" f"J1,{default_ja_email(election_id)}\n"
            ).encode()
        ),
        election_id,
    )
    assert_ok(rv)

    jurisdictions = (
        Jurisdiction.query.filter_by(election_id=election_id)
        .order_by(Jurisdiction.name)
        .all()
    )

    assert len(jurisdictions) == 1
    return [j.id for j in jurisdictions]


@pytest.fixture
def manifests(client: FlaskClient, election_id: str, jurisdiction_ids: List[str]):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = upload_ballot_manifest(
        client,
        io.BytesIO(
            b"Batch Name,Number of Ballots\n"
            b"Batch 1,1000\n"
            b"Batch 2,1000\n"
            b"Batch 3,1000\n"
            b"Batch 4,1000\n"
            b"Batch 5,200\n"
            b"Batch 6,200\n"
            b"Batch 7,200\n"
            b"Batch 8,200\n"
            b"Batch 9,200\n"
        ),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)


@pytest.fixture
def batch_tallies(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_ids: List[str],  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    batch_tallies_file = (
        b"Batch Name,candidate 1,candidate 2,candidate 3\n"
        b"Batch 1,1000,500,500\n"
        b"Batch 2,1000,500,500\n"
        b"Batch 3,1000,500,500\n"
        b"Batch 4,1000,500,500\n"
        b"Batch 5,200,100,100\n"
        b"Batch 6,200,100,100\n"
        b"Batch 7,200,100,100\n"
        b"Batch 8,200,100,100\n"
        b"Batch 9,200,100,100\n"
    )
    rv = upload_batch_tallies(
        client,
        io.BytesIO(batch_tallies_file),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)


def test_batch_comparison_single_jurisdiction_discrepancies(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    contest_id: str,
    round_1_id: str,
):
    rv = client.get(f"/api/election/{election_id}/contest")
    contests = json.loads(rv.data)["contests"]
    choice_names = [choice["name"] for choice in contests[0]["choices"]]
    choice_ids = [choice["id"] for choice in contests[0]["choices"]]

    # Audit batches
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches"
    )
    batches = json.loads(rv.data)["batches"]

    batch_tallies = Jurisdiction.query.get(jurisdiction_ids[0]).batch_tallies

    for batch in batches:
        results = batch_tallies[batch["name"]][contest_id]
        del results["ballots"]
        results[choice_ids[0]] = results[choice_ids[0]] - 1
        rv = put_json(
            client,
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/{batch['id']}/results",
            [{"name": "Tally Sheet #1", "results": results}],
        )
        assert_ok(rv)

    # Discrepancies should show before finalizing
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/discrepancy")
    discrepancies = json.loads(rv.data)
    for batch in batches:
        assert discrepancies[jurisdiction_ids[0]][batches[0]["name"]][contest_id][
            "discrepancies"
        ] == {
            choice_ids[0]: 1,
            choice_ids[1]: 0,
            choice_ids[2]: 0,
        }

    rv = client.get(f"/api/election/{election_id}/discrepancy-report")
    discrepancy_report = rv.data.decode("utf-8")
    expected_discrepancies = {
        "J1": {
            batch["name"]: {
                choice_names[0]: 1,
                choice_names[1]: 0,
                choice_names[2]: 0,
            }
            for batch in batches
        }
    }
    check_discrepancies(
        discrepancy_report, expected_discrepancies, contests[0]["choices"]
    )
