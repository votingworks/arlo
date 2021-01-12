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

    print(f"Jurisdiction: {jurisdiction.name}")

    print(f"Audit boards: {len(jurisdiction.audit_boards)}")
    if len(jurisdiction.audit_boards) == 0:
        print("Jurisdiction has no audit boards")
        sys.exit()

    num_audited_ballots = (
        SampledBallot.query.filter(SampledBallot.status != BallotStatus.NOT_AUDITED)
        .join(Batch)
        .filter_by(jurisdiction_id=jurisdiction_id)
        .count()
    )
    print(f"Jurisdiction has audited {num_audited_ballots} ballots so far")
    if num_audited_ballots > 0:
        print("Can't clear audit boards after ballots have been audited")
        sys.exit(1)

    if input("Are you sure you want to clear these audit boards? [y/n]") != "y":
        sys.exit()

    print("Clearing audit boards")
    AuditBoard.query.filter_by(jurisdiction_id=jurisdiction_id).delete()
    db_session.commit()
