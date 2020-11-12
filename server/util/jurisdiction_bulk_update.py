import uuid
from typing import Tuple, List
from ..models import *  # pylint: disable=wildcard-import
from ..util.process_file import process_file
from ..util.csv_parse import parse_csv, CSVValueType, CSVColumnType


JURISDICTION_NAME = "Jurisdiction"
ADMIN_EMAIL = "Admin Email"

JURISDICTIONS_COLUMNS = [
    CSVColumnType("Jurisdiction", CSVValueType.TEXT),
    CSVColumnType("Admin Email", CSVValueType.EMAIL),
]


def process_jurisdictions_file(session, election: Election, file: File) -> None:
    assert election.jurisdictions_file_id == file.id

    def process():
        jurisdictions_csv = parse_csv(
            election.jurisdictions_file.contents, JURISDICTIONS_COLUMNS
        )

        bulk_update_jurisdictions(
            session,
            election,
            [(row[JURISDICTION_NAME], row[ADMIN_EMAIL]) for row in jurisdictions_csv],
        )

    process_file(session, file, process)


def bulk_update_jurisdictions(
    session, election: Election, name_and_admin_email_pairs: List[Tuple[str, str]]
) -> List[JurisdictionAdministration]:
    """
    Updates the jurisdictions for an election all at once. Requires a SQLAlchemy session to use,
    and uses a nested transaction to ensure the changes made are atomic. Depending on your
    session configuration, you may need to explicitly call `commit()` on the session to flush
    changes to the database.
    """
    with session.begin_nested():
        # Clear existing admins.
        session.query(JurisdictionAdministration).filter(
            JurisdictionAdministration.jurisdiction_id.in_(
                Jurisdiction.query.filter(Jurisdiction.election == election).values(
                    Jurisdiction.id
                )
            )
        ).delete(synchronize_session="fetch")
        new_admins: List[JurisdictionAdministration] = []

        for (name, email) in name_and_admin_email_pairs:
            # Find or create the user for this jurisdiction.
            user = session.query(User).filter_by(email=email.lower()).one_or_none()

            if not user:
                user = User(id=str(uuid.uuid4()), email=email)
                session.add(user)

            # Find or create the jurisdiction by name.
            jurisdiction = Jurisdiction.query.filter_by(
                election=election, name=name
            ).one_or_none()

            if not jurisdiction:
                jurisdiction = Jurisdiction(
                    id=str(uuid.uuid4()), election=election, name=name
                )
                session.add(jurisdiction)

            # Link the user to the jurisdiction as an admin.
            admin = JurisdictionAdministration(jurisdiction=jurisdiction, user=user)
            session.add(admin)
            new_admins.append(admin)

        # Delete unmanaged jurisdictions.
        unmanaged_admin_id_records = (
            session.query(Jurisdiction)
            .outerjoin(JurisdictionAdministration)
            .filter(
                Jurisdiction.election == election,
                JurisdictionAdministration.jurisdiction_id.is_(None),
            )
            .with_entities(Jurisdiction.id)
            .all()
        )
        unmanaged_admin_ids = [id for (id,) in unmanaged_admin_id_records]
        session.query(Jurisdiction).filter(
            Jurisdiction.id.in_(unmanaged_admin_ids)
        ).delete(synchronize_session="fetch")

        return new_admins
