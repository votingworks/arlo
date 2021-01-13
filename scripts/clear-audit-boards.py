# pylint: disable=invalid-name
import sys

from server.models import *  # pylint: disable=wildcard-import
from server.database import db_session

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m scripts.clear-audit-boards <jurisdiction_id>")
        sys.exit(1)

    jurisdiction_id = sys.argv[1]
    jurisdiction = Jurisdiction.query.get(jurisdiction_id)
    if not jurisdiction:
        print("Jurisdiction not found")
        sys.exit(1)

    print(f"Org: {jurisdiction.election.organization.name}")
    print(f"Audit: {jurisdiction.election.audit_name}")
    print(f"Jurisdiction: {jurisdiction.name}")

    print(f"Audit boards: {len(jurisdiction.audit_boards)}")
    if len(jurisdiction.audit_boards) == 0:
        print("Jurisdiction has no audit boards")
        sys.exit()

    audited_ballots = (
        SampledBallot.query.filter(SampledBallot.status != BallotStatus.NOT_AUDITED)
        .join(Batch)
        .filter_by(jurisdiction_id=jurisdiction_id)
        .all()
    )
    print(f"Jurisdiction has audited {len(audited_ballots)} ballots so far")
    if len(audited_ballots) > 0:
        if (
            input("Do you want to clear the audit results for these ballots? [y/n]")
            != "y"
        ):
            sys.exit()
        if (
            input(
                "Are you sure want to clear the audit results for these ballots? [y/n]"
            )
            != "y"
        ):
            sys.exit()
        for ballot in audited_ballots:
            ballot.status = BallotStatus.NOT_AUDITED
            ballot.interpretations = []
        db_session.commit()

    if input("Are you sure you want to clear these audit boards? [y/n]") != "y":
        sys.exit()

    print("Clearing audit boards")
    AuditBoard.query.filter_by(jurisdiction_id=jurisdiction_id).delete()
    db_session.commit()
