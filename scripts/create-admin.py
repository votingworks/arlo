# pylint: disable=invalid-name
# type: ignore
import sys, uuid

from server.models import User, AuditAdministration, db

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python -m scripts.create-admin <org_id> <user_email>")
        sys.exit(1)

    org_id, email = sys.argv[1:]  # pylint: disable=unbalanced-tuple-unpacking
    u = User(id=str(uuid.uuid4()), email=email, external_id=email)
    audit_admin = AuditAdministration(user_id=u.id, organization_id=org_id)
    db.session.add(u)
    db.session.add(audit_admin)
    db.session.commit()

    print(u.id)
    print("Now add the user to auth0: https://manage.auth0.com/")
    print("For staging users, user the arlo-aa-staging tenant.")
    print("For prod users, use the arlo-aa tenant.")
