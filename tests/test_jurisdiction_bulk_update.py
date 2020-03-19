from util.jurisdiction_bulk_update import bulk_update_jurisdictions
from arlo_server.models import (
    Election,
    Jurisdiction,
    JurisdictionAdministration,
    Organization,
    User,
)
import arlo_server
import pytest
import uuid


@pytest.fixture
def db():
    with arlo_server.app.app_context():
        arlo_server.db.drop_all()
        arlo_server.db.create_all()

    yield arlo_server.db

    arlo_server.db.session.commit()


def test_first_update(db):
    org = Organization(id=str(uuid.uuid4()), name="Test Org")
    election = Election(id=str(uuid.uuid4()), audit_name="Test Audit", organization=org)
    new_admins = bulk_update_jurisdictions(
        db.session, election, [("Jurisdiction #1", "bob.harris@ca.gov")]
    )
    db.session.commit()

    assert [(admin.jurisdiction.name, admin.user.email) for admin in new_admins] == [
        ("Jurisdiction #1", "bob.harris@ca.gov")
    ]

    assert User.query.count() == 1
    assert Jurisdiction.query.count() == 1
    assert JurisdictionAdministration.query.count() == 1


def test_idempotent(db):
    org = Organization(id=str(uuid.uuid4()), name="Test Org")
    election = Election(id=str(uuid.uuid4()), audit_name="Test Audit", organization=org)

    # Do it once.
    bulk_update_jurisdictions(
        db.session, election, [("Jurisdiction #1", "bob.harris@ca.gov")]
    )
    db.session.commit()

    user = User.query.one()
    jurisdiction = Jurisdiction.query.one()

    # Do the same thing again.
    bulk_update_jurisdictions(
        db.session, election, [("Jurisdiction #1", "bob.harris@ca.gov")]
    )

    assert User.query.one() == user
    assert Jurisdiction.query.one() == jurisdiction


def test_remove_outdated_jurisdictions(db):
    org = Organization(id=str(uuid.uuid4()), name="Test Org")
    election = Election(id=str(uuid.uuid4()), audit_name="Test Audit", organization=org)

    # Add jurisdictions.
    bulk_update_jurisdictions(
        db.session, election, [("Jurisdiction #1", "bob.harris@ca.gov")]
    )
    db.session.commit()

    # Delete jurisdictions.
    new_admins = bulk_update_jurisdictions(db.session, election, [])

    assert new_admins == []
    assert User.query.count() == 1  # keep the user
    assert Jurisdiction.query.count() == 0
    assert JurisdictionAdministration.query.count() == 0
