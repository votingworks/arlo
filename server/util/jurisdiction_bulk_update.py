import uuid
from typing import Tuple, List
from ..db.setup import db_session
from ..db.models import *
from ..db.views import ElectionView
from ..util.process_file import process_file
from ..util.csv_parse import parse_csv, CSVValueType, CSVColumnType


JURISDICTION_NAME = "Jurisdiction"
ADMIN_EMAIL = "Admin Email"

JURISDICTIONS_COLUMNS = [
    CSVColumnType("Jurisdiction", CSVValueType.TEXT),
    CSVColumnType("Admin Email", CSVValueType.EMAIL),
]


def process_jurisdictions_file(session, view: ElectionView, file: File) -> None:
    assert view.election.jurisdictions_file_id == file.id

    def process():
        jurisdictions_csv = parse_csv(
            view.election.jurisdictions_file.contents, JURISDICTIONS_COLUMNS
        )

        bulk_update_jurisdictions(
            view,
            [(row[JURISDICTION_NAME], row[ADMIN_EMAIL]) for row in jurisdictions_csv],
        )

    process_file(session, file, process)


def bulk_update_jurisdictions(
    view: ElectionView, name_and_admin_email_pairs: List[Tuple[str, str]]
) -> List[JurisdictionAdministration]:
    """
    Updates the jurisdictions for an election all at once. Uses a nested
    transaction to ensure the changes made are atomic. Depending on your
    session configuration, you may need to explicitly call `commit()` on the
    session to flush changes to the database.
    """
    with db_session.begin_nested():
        # Clear existing admins.
        existing_admins = view.JurisdictionAdministration_query.all()
        for admin in existing_admins:
            db_session.delete(admin)

        new_admins: List[JurisdictionAdministration] = []

        for (name, email) in name_and_admin_email_pairs:
            # Find or create the user for this jurisdiction.
            user = User.unpermissioned_query.filter_by(
                email=email.lower()
            ).one_or_none()

            if not user:
                user = User(id=str(uuid.uuid4()), email=email)
                db_session.add(user)

            # Find or create the jurisdiction by name.
            jurisdiction = view.Jurisdiction_query.filter_by(name=name).one_or_none()

            if not jurisdiction:
                jurisdiction = Jurisdiction(
                    id=str(uuid.uuid4()), election=view.election, name=name
                )
                db_session.add(jurisdiction)

            # Link the user to the jurisdiction as an admin.
            admin = JurisdictionAdministration(jurisdiction=jurisdiction, user=user)
            db_session.add(admin)
            new_admins.append(admin)

        # Delete unmanaged jurisdictions.
        unmanaged_jurisdictions = (
            view.Jurisdiction_query.outerjoin(JurisdictionAdministration)
            .filter(JurisdictionAdministration.jurisdiction_id.is_(None))
            .all()
        )
        for jurisdiction in unmanaged_jurisdictions:
            db_session.delete(jurisdiction)

        return new_admins
