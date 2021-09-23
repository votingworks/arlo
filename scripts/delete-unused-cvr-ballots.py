# pylint: disable=invalid-name
from server.models import Election, AuditType
from server.api.rounds import (
    delete_unsampled_cvrs,
    get_current_round,
    is_audit_complete,
)
from server.database import db_session

orgs = set()
if __name__ == "__main__":
    for election in Election.query.all():
        round = get_current_round(election)
        if election.audit_type in [AuditType.BALLOT_COMPARISON, AuditType.HYBRID]:
            if round and is_audit_complete(round):
                print(f"Deleting CVRs for {election.audit_name}")
                print(delete_unsampled_cvrs(election))
            print(f"Audit not complete: {election.audit_name}")
            orgs.add(election.organization.name)
        else:
            print(f"Skipping {election.audit_name}")
            continue
    db_session.commit()
    for org in orgs:
        print(org)
    # print("Done!")
