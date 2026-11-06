import json
from flask.testing import FlaskClient

from ...database import db_session
from ...models import *
from ..helpers import *


# A jurisdiction's audit of its first contest, with every batch tallied as
# reported except the first, which is off by one, finalized
class Audit:
    def __init__(
        self, client: FlaskClient, election_id: str, jurisdiction_id: str, round_id: str
    ):
        self.client = client
        self.election_id = election_id
        self.jurisdiction_id = jurisdiction_id
        self.round_id = round_id
        self.finalize_url = f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_id}/batches/finalize"
        self.log_in_ja()
        rv = client.get(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/contest"
        )
        self.contest = json.loads(rv.data)["contests"][0]
        rv = client.get(
            f"/api/election/{election_id}/jurisdiction/{jurisdiction_id}/round/{round_id}/batches"
        )
        self.batches = json.loads(rv.data)["batches"]
        self.batch_tallies = Jurisdiction.query.get(jurisdiction_id).batch_tallies
        first_choice_id = self.contest["choices"][0]["id"]
        self.off_by_one = {
            **self.reported_results(self.batches[0]),
            first_choice_id: self.reported_results(self.batches[0])[first_choice_id]
            - 1,
        }
        self.record(self.batches[0], self.off_by_one)
        for batch in self.batches[1:]:
            self.record(batch, self.reported_results(batch))
        self.finalize()

    def log_in_ja(self):
        set_logged_in_user(
            self.client, UserType.JURISDICTION_ADMIN, default_ja_email(self.election_id)
        )

    def log_in_aa(self):
        set_logged_in_user(self.client, UserType.AUDIT_ADMIN, DEFAULT_AA_EMAIL)

    def reported_results(self, batch):
        return {
            choice["id"]: self.batch_tallies[batch["name"]][self.contest["id"]][
                choice["id"]
            ]
            for choice in self.contest["choices"]
        }

    def record(self, batch, results):
        self.log_in_ja()
        rv = put_batch_results(
            self.client,
            self.election_id,
            self.jurisdiction_id,
            self.round_id,
            batch["id"],
            [results],
        )
        assert_ok(rv)

    def finalize(self):
        self.log_in_ja()
        rv = post_json(self.client, self.finalize_url)
        assert_ok(rv)

    def unfinalize(self):
        self.log_in_aa()
        rv = self.client.delete(self.finalize_url)
        assert_ok(rv)

    def statuses(self):
        self.log_in_aa()
        rv = self.client.get(f"/api/election/{self.election_id}/discrepancy")
        return {
            batch["name"]: batch["discrepancies"][self.contest["id"]]["status"]
            for batch in json.loads(rv.data)[self.jurisdiction_id]["batches"].values()
        }

    def set_status(self, batch, status):
        contest_status = BatchContestStatus.query.get((batch["id"], self.contest["id"]))
        contest_status.status = status
        db_session.commit()

    def mark(self, batch, status):
        self.log_in_aa()
        return put_json(
            self.client,
            f"/api/election/{self.election_id}/jurisdiction/{self.jurisdiction_id}/round/{self.round_id}/batches/{batch['id']}/discrepancy-status",
            {"contestId": self.contest["id"], "status": status},
        )


def test_batch_contest_statuses_follow_the_tallies(
    client: FlaskClient,
    election_id: str,
    jurisdiction_ids: list[str],
    round_1_id: str,
):
    audit = Audit(client, election_id, jurisdiction_ids[0], round_1_id)
    batches, statuses, record, finalize, unfinalize, set_status = (
        audit.batches,
        audit.statuses,
        audit.record,
        audit.finalize,
        audit.unfinalize,
        audit.set_status,
    )
    reported_results, off_by_one = audit.reported_results, audit.off_by_one

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
    ]

    # Only those two decisions, only for audit admins
    rv = audit.mark(off, "MATCHES")
    assert rv.status_code == 400
    rv = put_json(
        client,
        f"/api/election/{election_id}/jurisdiction/{jurisdiction_ids[0]}/round/{round_1_id}/batches/not-a-batch/discrepancy-status",
        {"contestId": audit.contest["id"], "status": "ACCEPTED"},
    )
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
