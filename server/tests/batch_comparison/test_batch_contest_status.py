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


def test_audit_admin_marks_a_batch_contest(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
    round_1_id: str,
):
    audit = Audit(client, election_id, jurisdiction_ids[0], round_1_id)
    off, fine = audit.batches[0], audit.batches[1]

    rv = audit.mark(off, "JURISDICTION_CONTACTED")
    assert_ok(rv)
    assert audit.statuses()[off["name"]] == "JURISDICTION_CONTACTED"
    # Marking it contacted again changes nothing, so it isn't noted again
    rv = audit.mark(off, "JURISDICTION_CONTACTED")
    assert_ok(rv)
    rv = audit.mark(off, "ACCEPTED")
    assert_ok(rv)
    assert audit.statuses()[off["name"]] == "ACCEPTED"
    # Accepting can be undone
    rv = audit.mark(off, "NEEDS_REVIEW")
    assert_ok(rv)
    assert audit.statuses()[off["name"]] == "NEEDS_REVIEW"

    # A batch contest that matches has nothing to decide
    rv = audit.mark(fine, "ACCEPTED")
    assert_ok(rv)
    assert audit.statuses()[fine["name"]] == "MATCHES"

    # Each decision leaves a note
    assert [
        note.text
        for note in JurisdictionNote.query.filter_by(
            jurisdiction_id=jurisdiction_ids[0]
        ).order_by(JurisdictionNote.created_at)
    ] == [
        "Finalized tallies",
        f"Marked {off['name']} for {audit.contest['name']} contacted",
        f"Accepted {off['name']} for {audit.contest['name']}",
        f"Marked {off['name']} for {audit.contest['name']} needs review",
    ]

    # Only those decisions, only for audit admins, only on finalized tallies
    rv = audit.mark(off, "MATCHES")
    assert rv.status_code == 400
    audit.unfinalize()
    rv = audit.mark(off, "NEEDS_REVIEW")
    assert rv.status_code == 409
    audit.finalize()
    rv = audit.mark({"id": "not-a-batch"}, "ACCEPTED")
    assert rv.status_code == 404
    audit.log_in_ja()
    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/{off['id']}/discrepancy-status",
        {"contestId": audit.contest["id"], "status": "ACCEPTED"},
    )
    assert rv.status_code == 403


def test_finishing_a_round_accepts_what_is_still_under_review(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
    round_1_id: str,
):
    audits = [
        Audit(client, election_id, jurisdiction_id, round_1_id)
        for jurisdiction_id in jurisdiction_ids[:2]
    ]
    rv = audits[0].mark(audits[0].batches[0], "JURISDICTION_CONTACTED")
    assert_ok(rv)

    audits[0].log_in_aa()
    rv = client.post(f"/api/election/{election_id}/round/current/finish")
    assert_ok(rv)
    # The decisions are closed with the round
    rv = audits[0].mark(audits[0].batches[0], "NEEDS_REVIEW")
    assert rv.status_code == 409
    for audit in audits:
        assert audit.statuses() == {
            audit.batches[0]["name"]: "ACCEPTED",
            **{batch["name"]: "MATCHES" for batch in audit.batches[1:]},
        }
        assert (
            JurisdictionNote.query.filter_by(jurisdiction_id=audit.jurisdiction_id)
            .order_by(JurisdictionNote.created_at.desc())
            .first()
            .text
            == "Accepted remaining discrepancies when round 1 finished"
        )


def test_undoing_a_round_start_forgets_its_statuses(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
    round_1_id: str,
):
    audit = Audit(client, election_id, jurisdiction_ids[0], round_1_id)
    statuses = BatchContestStatus.query.join(Batch).filter_by(
        jurisdiction_id=jurisdiction_ids[0]
    )
    assert statuses.count() == len(audit.batches)

    audit.log_in_aa()
    rv = client.delete(f"/api/election/{election_id}/round/current")
    assert_ok(rv)
    assert statuses.count() == 0


def test_combining_batches_forgets_their_statuses(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
    round_1_id: str,
):
    audit = Audit(client, election_id, jurisdiction_ids[0], round_1_id)
    off_by_one_batch = audit.batches[0]
    assert_ok(audit.mark(off_by_one_batch, "ACCEPTED"))
    audit.unfinalize()

    unsampled_batch = (
        Batch.query.filter_by(jurisdiction_id=jurisdiction_ids[0])
        .filter(~Batch.draws.any())
        .order_by(Batch.name)
        .first()
    )
    sub_batch_statuses = BatchContestStatus.query.filter(
        BatchContestStatus.batch_id.in_([off_by_one_batch["id"], unsampled_batch.id])
    )
    combined_batches_url = (
        f"/api/support/jurisdictions/{jurisdiction_ids[0]}/combined-batches"
    )
    set_support_user(client, DEFAULT_SUPPORT_EMAIL)
    rv = post_json(
        client,
        combined_batches_url,
        dict(
            name="Combined Batch 1",
            subBatchIds=[off_by_one_batch["id"], unsampled_batch.id],
        ),
    )
    assert_ok(rv)
    assert sub_batch_statuses.count() == 0

    # The combined batch is judged from scratch, not by the acceptance
    audit.log_in_ja()
    rv = client.get(
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches"
    )
    combined_batch = next(
        batch
        for batch in json.loads(rv.data)["batches"]
        if batch["name"] == "Combined Batch 1"
    )
    unsampled_results = audit.reported_results({"name": unsampled_batch.name})
    audit.record(
        combined_batch,
        {
            choice_id: votes + unsampled_results[choice_id]
            for choice_id, votes in audit.off_by_one.items()
        },
    )
    audit.finalize()
    assert audit.statuses()["Combined Batch 1"] == "NEEDS_REVIEW"

    # And so are the sub-batches once uncombined
    assert_ok(audit.mark(combined_batch, "ACCEPTED"))
    audit.unfinalize()
    set_support_user(client, DEFAULT_SUPPORT_EMAIL)
    assert_ok(client.delete(f"{combined_batches_url}/Combined Batch 1"))
    assert sub_batch_statuses.count() == 0

    audit.record(off_by_one_batch, audit.off_by_one)
    audit.finalize()
    assert audit.statuses()[off_by_one_batch["name"]] == "NEEDS_REVIEW"
