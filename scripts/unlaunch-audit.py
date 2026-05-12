# pylint: disable=invalid-name
import sys

from server.models import *  # pylint: disable=wildcard-import
from server.database import db_session
from server.api.shared import get_current_round

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m scripts.unlaunch-audit <election_id>")
        sys.exit(1)

    election_id = sys.argv[1]
    election = Election.query.get(election_id)
    if not election:
        print("Audit not found")
        sys.exit(1)

    if election.audit_type != AuditType.BATCH_COMPARISON:
        print(
            f"This script only supports batch comparison audits, not {election.audit_type}."
        )
        sys.exit(1)

    print(f"Org: {election.organization.name}")
    print(f"Audit: {election.audit_name}")
    print(f"Audit type: {election.audit_type}")

    round = get_current_round(election)
    if not round:
        print("Audit has not started yet")
        sys.exit(1)

    print(f"Current round: {round.round_num}")

    audit_board_count = AuditBoard.query.filter_by(round_id=round.id).count()
    sampled_batch_ids = [
        row[0]
        for row in SampledBatchDraw.query.filter_by(round_id=round.id)
        .with_entities(SampledBatchDraw.batch_id)
        .distinct()
        .all()
    ]
    tally_sheet_count = (
        BatchResultTallySheet.query.filter(
            BatchResultTallySheet.batch_id.in_(sampled_batch_ids)
        ).count()
        if sampled_batch_ids
        else 0
    )

    print(f"Audit boards across all jurisdictions: {audit_board_count}")
    print(f"Sampled batches: {len(sampled_batch_ids)}")
    print(f"Batch result tally sheets on sampled batches: {tally_sheet_count}")

    print()
    print("This will, in a single transaction:")
    print("  1. Delete all batch result tally sheets on sampled batches")
    print("  2. Delete the round (cascades AuditBoard, SampledBatchDraw,")
    print("     RoundContest, BatchResultsFinalized)")
    print()
    if (
        input(f"Unlaunch round {round.round_num} of '{election.audit_name}'? [y/n] ")
        != "y"
    ):
        sys.exit()
    if input("Are you sure? This is irreversible. [y/n] ") != "y":
        sys.exit()

    try:
        if tally_sheet_count > 0:
            print("Deleting batch result tally sheets on sampled batches...")
            BatchResultTallySheet.query.filter(
                BatchResultTallySheet.batch_id.in_(sampled_batch_ids)
            ).delete(synchronize_session=False)

        print("Deleting round...")
        db_session.delete(round)

        db_session.commit()
        print(f"Done. Audit '{election.audit_name}' is back in pre-launch state.")
    except Exception:
        db_session.rollback()
        print("Error during unlaunch — transaction rolled back, no changes made.")
        raise
