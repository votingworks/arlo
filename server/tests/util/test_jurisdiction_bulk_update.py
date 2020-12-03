from flask.testing import FlaskClient
from ...auth import UserType
from ...util.jurisdiction_bulk_update import bulk_update_jurisdictions
from ...models import *  # pylint: disable=wildcard-import
from ...database import db_session
from ..helpers import *  # pylint: disable=wildcard-import


def test_first_update(election_id: str):
    election = Election.query.get(election_id)
    new_admins = bulk_update_jurisdictions(
        db_session, election, [("Jurisdiction #1", "bob.harris@ca.gov")]
    )
    db_session.commit()

    assert [(admin.jurisdiction.name, admin.user.email) for admin in new_admins] == [
        ("Jurisdiction #1", "bob.harris@ca.gov")
    ]

    assert User.query.filter_by(email="bob.harris@ca.gov").first()
    jurisdictions = Jurisdiction.query.filter_by(election_id=election_id).all()
    assert len(jurisdictions) == 1
    assert (
        JurisdictionAdministration.query.filter_by(
            jurisdiction_id=jurisdictions[0].id
        ).count()
        == 1
    )


def test_idempotent(election_id: str):
    election = Election.query.get(election_id)
    # Do it once.
    bulk_update_jurisdictions(db_session, election, [("Jurisdiction #1", "ja1@ca.gov")])
    db_session.commit()

    user = User.query.filter_by(email="ja1@ca.gov").one()
    jurisdiction = Jurisdiction.query.filter_by(election_id=election_id).first()

    # Do the same thing again.
    bulk_update_jurisdictions(db_session, election, [("Jurisdiction #1", "ja1@ca.gov")])

    assert User.query.filter_by(email="ja1@ca.gov").one() == user
    assert Jurisdiction.query.filter_by(election_id=election_id).first() == jurisdiction


def test_remove_outdated_jurisdictions(election_id):
    election = Election.query.get(election_id)
    # Add jurisdictions.
    bulk_update_jurisdictions(db_session, election, [("Jurisdiction #1", "ja2@ca.gov")])
    db_session.commit()

    # Delete jurisdictions.
    new_admins = bulk_update_jurisdictions(db_session, election, [])

    assert new_admins == []
    assert User.query.filter_by(email="ja2@ca.gov").first()  # keep the user
    assert Jurisdiction.query.filter_by(election_id=election_id).count() == 0


def test_dont_clobber_other_elections(client: FlaskClient, election_id, org_id):
    election = Election.query.get(election_id)

    set_logged_in_user(client, UserType.AUDIT_ADMIN, user_key=DEFAULT_AA_EMAIL)
    other_election_id = create_election(
        client, audit_name="Test Audit 2", organization_id=org_id
    )
    other_election = Election.query.get(other_election_id)

    # Add jurisdictions.
    bulk_update_jurisdictions(
        db_session, election, [("Jurisdiction #1", "j1-ja@ca.gov")]
    )
    db_session.commit()

    # Add jurisdictions for other election
    bulk_update_jurisdictions(
        db_session, other_election, [("Jurisdiction #2", "j2-ja@ca.gov")]
    )
    db_session.commit()

    # Now change them
    bulk_update_jurisdictions(
        db_session, other_election, [("Jurisdiction #3", "j3-ja@ca.gov")]
    )
    db_session.commit()

    # Make sure first election admins were not clobbered
    assert (
        len(
            Jurisdiction.query.filter_by(election_id=election.id)
            .first()
            .jurisdiction_administrations
        )
        == 1
    )
