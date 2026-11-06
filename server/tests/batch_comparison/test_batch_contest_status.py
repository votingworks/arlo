import json
from flask.testing import FlaskClient

from ...models import *
from ..helpers import *


def test_batch_contest_statuses_follow_the_tallies(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
    round_1_id: str,
):
    audit = Audit(client, election_id, jurisdiction_ids[0], round_1_id)
    batches = audit.batches
    assert audit.statuses() == {
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
    audit.unfinalize()
    assert audit.statuses()[batches[0]["name"]] == "RE_TALLYING"
    assert set(audit.statuses().values()) == {"RE_TALLYING", "MATCHES"}
    # Support still counts the one discrepancy while the batches re-tally
    set_support_user(client, DEFAULT_SUPPORT_EMAIL)
    rv = client.get(f"/api/support/elections/{election_id}/round-progress")
    assert json.loads(rv.data)["discrepancyCount"] == 1
    clear_support_user(client)
    audit.record(batches[0], audit.reported_results(batches[0]))
    audit.finalize()
    assert set(audit.statuses().values()) == {"MATCHES"}
    audit.unfinalize()
    audit.record(batches[0], audit.off_by_one)
    audit.finalize()
    assert audit.statuses()[batches[0]["name"]] == "NEEDS_REVIEW"

    # An audit admin's acceptance survives unfinalizing and re-finalizing;
    # having contacted the jurisdiction doesn't, since the re-finalize is the
    # jurisdiction's answer
    audit.set_status(batches[0], BatchDiscrepancyStatus.ACCEPTED)
    audit.unfinalize()
    assert audit.statuses()[batches[0]["name"]] == "ACCEPTED"
    audit.finalize()
    assert audit.statuses()[batches[0]["name"]] == "ACCEPTED"
    audit.set_status(batches[0], BatchDiscrepancyStatus.JURISDICTION_CONTACTED)
    audit.unfinalize()
    assert audit.statuses()[batches[0]["name"]] == "RE_TALLYING"
    audit.finalize()
    assert audit.statuses()[batches[0]["name"]] == "NEEDS_REVIEW"
