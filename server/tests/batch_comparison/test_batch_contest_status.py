import json
from flask.testing import FlaskClient

from ...database import db_session
from ...models import *
from ..helpers import *


def test_batch_contest_statuses_follow_the_tallies(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
    round_1_id: str,
):
    jurisdiction_id = jurisdiction_ids[0]
    finalize_url = f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_1_id}/batches/finalize"
    set_logged_in_user(
        client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
    )
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/contest"
    )
    contest = json.loads(rv.data)["contests"][0]
    choice_ids = [choice["id"] for choice in contest["choices"]]
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_1_id}/batches"
    )
    batches = json.loads(rv.data)["batches"]
    batch_tallies = Jurisdiction.query.get(jurisdiction_id).batch_tallies

    def reported_results(batch):
        return {
            choice_id: batch_tallies[batch["name"]][contest["id"]][choice_id]
            for choice_id in choice_ids
        }

    def record(batch, results):
        set_logged_in_user(
            client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
        )
        rv = put_batch_results(
            client, election_id, jurisdiction_id, round_1_id, batch["id"], [results]
        )
        assert_ok(rv)

    def finalize():
        set_logged_in_user(
            client, UserType.JURISDICTION_ADMIN, default_ja_email(election_id)
        )
        rv = post_json(client, finalize_url)
        assert_ok(rv)

    def unfinalize():
        set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
        rv = client.delete(finalize_url)
        assert_ok(rv)

    def statuses():
        set_logged_in_user(client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)
        rv = client.get(f"/api/election/{election_id}/discrepancy")
        return {
            batch["name"]: batch["discrepancies"][contest["id"]]["status"]
            for batch in json.loads(rv.data)[jurisdiction_id]["batches"].values()
        }

    def set_status(batch, status):
        contest_status = BatchContestStatus.query.get((batch["id"], contest["id"]))
        contest_status.status = status
        db_session.commit()

    # Every batch matches but the first, which is off by one
    off_by_one = {
        **reported_results(batches[0]),
        choice_ids[0]: reported_results(batches[0])[choice_ids[0]] - 1,
    }
    record(batches[0], off_by_one)
    for batch in batches[1:]:
        record(batch, reported_results(batch))
    finalize()
    assert statuses() == {
        batches[0]["name"]: "NEEDS_REVIEW",
        **{batch["name"]: "MATCHES" for batch in batches[1:]},
    }
    finalize_record = (
        ActivityLogRecord.query.filter_by(
            organization_id=Election.query.get(election_id).organization_id,
            activity_name="FinalizeBatchResults",
        )
        .order_by(ActivityLogRecord.timestamp.desc())
        .first()
    )
    assert finalize_record.info["num_batches_with_discrepancies"] == 1
    set_support_user(client, DEFAULT_SUPPORT_EMAIL)
    rv = client.get(f"/api/support/elections/{election_id}/round-progress")
    assert json.loads(rv.data)["discrepancyCount"] == 1
    clear_support_user(client)

    # Unfinalizing reopens the batch under review; a re-tally that fixes it
    # makes it match, and one that leaves it off again reopens it
    unfinalize()
    assert statuses()[batches[0]["name"]] == "RE_TALLYING"
    assert set(statuses().values()) == {"RE_TALLYING", "MATCHES"}
    # Support still counts the one discrepancy while the batches re-tally
    set_support_user(client, DEFAULT_SUPPORT_EMAIL)
    rv = client.get(f"/api/support/elections/{election_id}/round-progress")
    assert json.loads(rv.data)["discrepancyCount"] == 1
    clear_support_user(client)
    record(batches[0], reported_results(batches[0]))
    finalize()
    assert set(statuses().values()) == {"MATCHES"}
    unfinalize()
    record(batches[0], off_by_one)
    finalize()
    assert statuses()[batches[0]["name"]] == "NEEDS_REVIEW"

    # An audit admin's acceptance survives unfinalizing and re-finalizing;
    # having contacted the jurisdiction doesn't, since the re-finalize is the
    # jurisdiction's answer
    set_status(batches[0], BatchDiscrepancyStatus.ACCEPTED)
    unfinalize()
    assert statuses()[batches[0]["name"]] == "ACCEPTED"
    finalize()
    assert statuses()[batches[0]["name"]] == "ACCEPTED"
    set_status(batches[0], BatchDiscrepancyStatus.JURISDICTION_CONTACTED)
    unfinalize()
    assert statuses()[batches[0]["name"]] == "RE_TALLYING"
    finalize()
    assert statuses()[batches[0]["name"]] == "NEEDS_REVIEW"
