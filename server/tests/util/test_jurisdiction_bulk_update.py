import uuid
from ...util.jurisdiction_bulk_update import bulk_update_jurisdictions
from ...models import (
    Organization,
    Election,
    User,
    Jurisdiction,
    JurisdictionAdministration,
)
from ...database import db_session


def test_first_update():
    org = Organization(id=str(uuid.uuid4()), name="Test Org")
    election = Election(
        id=str(uuid.uuid4()),
        audit_name="Test Audit",
        organization=org,
        is_multi_jurisdiction=True,
    )
    new_admins = bulk_update_jurisdictions(
        db_session, election, [("Jurisdiction #1", "bob.harris@ca.gov")]
    )
    db_session.commit()

    assert [(admin.jurisdiction.name, admin.user.email) for admin in new_admins] == [
        ("Jurisdiction #1", "bob.harris@ca.gov")
    ]

    assert User.query.count() == 1
    assert Jurisdiction.query.count() == 1
    assert JurisdictionAdministration.query.count() == 1


def test_idempotent():
    org = Organization(id=str(uuid.uuid4()), name="Test Org")
    election = Election(
        id=str(uuid.uuid4()),
        audit_name="Test Audit",
        organization=org,
        is_multi_jurisdiction=True,
    )

    # Do it once.
    bulk_update_jurisdictions(
        db_session, election, [("Jurisdiction #1", "bob.harris@ca.gov")]
    )
    db_session.commit()

    user = User.query.one()
    jurisdiction = Jurisdiction.query.one()

    # Do the same thing again.
    bulk_update_jurisdictions(
        db_session, election, [("Jurisdiction #1", "bob.harris@ca.gov")]
    )

    assert User.query.one() == user
    assert Jurisdiction.query.one() == jurisdiction


def test_remove_outdated_jurisdictions():
    org = Organization(id=str(uuid.uuid4()), name="Test Org")
    election = Election(
        id=str(uuid.uuid4()),
        audit_name="Test Audit",
        organization=org,
        is_multi_jurisdiction=True,
    )

    # Add jurisdictions.
    bulk_update_jurisdictions(
        db_session, election, [("Jurisdiction #1", "bob.harris@ca.gov")]
    )
    db_session.commit()

    # Delete jurisdictions.
    new_admins = bulk_update_jurisdictions(db_session, election, [])

    assert new_admins == []
    assert User.query.count() == 1  # keep the user
    assert Jurisdiction.query.count() == 0
    assert JurisdictionAdministration.query.count() == 0
