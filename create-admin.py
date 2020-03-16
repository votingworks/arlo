# type: ignore
import sys, uuid

from arlo_server.models import User, AuditAdministration, db

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python create-admin.py <org_id> <user_email>")
        sys.exit(1)

    org_id, email = sys.argv[1:]
    u = User(id=str(uuid.uuid4()), email=email, external_id=email)
    audit_admin = AuditAdministration(user_id=u.id, organization_id=org_id)
    db.session.add(u)
    db.session.add(audit_admin)
    db.session.commit()

    print(u.id)
