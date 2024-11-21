from typing import List
import io
import pytest
from flask.testing import FlaskClient


from ...models import *  # pylint: disable=wildcard-import
from ..helpers import *  # pylint: disable=wildcard-import
from .conftest import TEST_CVRS
from .test_ballot_comparison import audit_all_ballots, check_discrepancies


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
            b"Tabulator,Batch Name,Number of Ballots\n"
            b"TABULATOR1,BATCH1,3\n"
            b"TABULATOR1,BATCH2,3\n"
            b"TABULATOR2,BATCH1,3\n"
            b"TABULATOR2,BATCH2,6"
        ),
        election_id,
        jurisdiction_ids[0],
    )
    assert_ok(rv)


@pytest.fixture
def cvrs(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    manifests,  # pylint: disable=unused-argument
):
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = upload_cvrs(
        client,
        io.BytesIO(TEST_CVRS.encode()),
        election_id,
        jurisdiction_ids[0],
        "DOMINION",
    )
    assert_ok(rv)


def test_ballot_comparison_single_jurisdiction_discrepancies(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: List[str],
    election_settings,  # pylint: disable=unused-argument
    manifests,  # pylint: disable=unused-argument
    cvrs,  # pylint: disable=unused-argument
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
                "jurisdictionIds": jurisdiction_ids,
                "isTargeted": True,
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Contest 2",
                "numWinners": 1,
                "jurisdictionIds": jurisdiction_ids,
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

    rv = post_json(
        client,
        f"/api/election/{election_id}/round",
        {
            "roundNum": 1,
            "sampleSizes": {
                target_contest_id: {"key": "custom", "size": 3, "prob": None}
            },
        },
    )
    assert_ok(rv)

    rv = client.get(
        f"/api/election/{election_id}/round",
    )
    round_1_id = json.loads(rv.data)["rounds"][0]["id"]

    # JM creates audit board
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = post_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/audit-board",
        [{"name": "Audit Board #1"}],
    )
    assert_ok(rv)

    # JM audits ballots
    round_1_audit_results = {
        ("J1", "TABULATOR2", "BATCH2", 2): ("0,1,0,1,0", (1, 1)),  # CVR: 1,1,1,1,1
        ("J1", "TABULATOR2", "BATCH2", 4): ("blank", (None, None)),
    }
    audit_all_ballots(
        round_1_id,
        round_1_audit_results,
        target_contest_id,
        opportunistic_contest_id,
    )
    db_session.commit()

    # Discrepancies should show before audit board sign off
    set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
    rv = client.get(f"/api/election/{election_id}/discrepancy")
    discrepancies = json.loads(rv.data)
    target_contest_discrepancies = discrepancies[jurisdiction_ids[0]][
        "TABULATOR2, BATCH2, Ballot 2"
    ][target_contest_id]
    contest_choices = contests[0]["choices"]
    assert target_contest_discrepancies["discrepancies"][contest_choices[0]["id"]] == 1

    rv = client.get(f"/api/election/{election_id}/discrepancy-report")
    discrepancy_report = rv.data.decode("utf-8")
    check_discrepancies(discrepancy_report, round_1_audit_results)
