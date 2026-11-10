"""
Queues jobs to reprocess every batch inventory CVR file in an audit.

Usage: python -m scripts.reprocess-batch-inventory-cvrs <election_id> <support_user_email> <audit_admin_email>
"""

import sys

from server import config
from server.api.batch_inventory import reprocess_batch_inventory_cvr_if_uploaded
from server.auth.auth_helpers import UserType
from server.database import db_session
from server.models import BatchInventoryData, Election

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(
            "Usage: python -m scripts.reprocess-batch-inventory-cvrs <election-id> <support-user-email> <audit-admin-email>"
        )
        sys.exit(1)

    # Otherwise the jobs would run here, with this machine's file storage config
    if config.RUN_BACKGROUND_TASKS_IMMEDIATELY:
        sys.exit("Unset RUN_BACKGROUND_TASKS_IMMEDIATELY first")

    election_id, support_user_email, audit_admin_email = sys.argv[1:]
    election = Election.query.get(election_id)
    if not election:
        sys.exit("Audit not found")
    print(f"Audit: {election.audit_name}")

    audit_admin_email = audit_admin_email.lower()
    audit_admin_emails = {
        audit_admin.user.email
        for audit_admin in election.organization.audit_administrations
    }
    if audit_admin_email not in audit_admin_emails:
        sys.exit(f"{audit_admin_email} isn't an audit admin for this audit's org")

    jurisdictions = [
        jurisdiction
        for jurisdiction in sorted(election.jurisdictions, key=lambda j: j.name)
        if (data := BatchInventoryData.query.get(jurisdiction.id)) and data.cvr_file
    ]
    # jurisdictions = [jurisdictions[0]]
    for jurisdiction in jurisdictions:
        print(f"  {jurisdiction.name}")

    print(
        f"Will be logged as: Support user {support_user_email} logged in as audit admin {audit_admin_email}"
    )
    if input(f"Reprocess {len(jurisdictions)} CVR file(s)? [y/n] ") != "y":
        sys.exit()

    user = (UserType.AUDIT_ADMIN, audit_admin_email)
    for jurisdiction in jurisdictions:
        # Reprocessing clears the sign-off, but we keep it, since this doesn't
        # change the batch inventory worksheet
        data = BatchInventoryData.query.get(jurisdiction.id)
        signed_off_at, sign_off_user_id = data.signed_off_at, data.sign_off_user_id
        reprocess_batch_inventory_cvr_if_uploaded(
            jurisdiction, user, support_user_email
        )
        data.signed_off_at = signed_off_at
        data.sign_off_user_id = sign_off_user_id
    db_session.commit()
    print(f"Queued {len(jurisdictions)} job(s)")
