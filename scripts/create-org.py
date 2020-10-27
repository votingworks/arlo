# pylint: disable=invalid-name
import sys
import uuid
from server.database import db_session
from server.models import Organization

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m scripts.create-org <org_name>")
        sys.exit(1)

    org = Organization(id=str(uuid.uuid4()), name=sys.argv[1])
    db_session.add(org)
    db_session.commit()
    print(org.id)
