# pylint: disable=invalid-name
import io
from server.models import *  # pylint: disable=wildcard-import
from server.database import db_session
from server.util.file import retrieve_file, store_file, timestamp_filename


def migrate_file(file, path):
    contents = file.contents.encode("utf-8")
    if not file.storage_path:
        storage_path = store_file(io.BytesIO(contents), path)
        file.storage_path = storage_path
        stored_file = retrieve_file(file.storage_path)
        assert stored_file.read() == contents
        return storage_path
    else:
        print("Already migrated")
        if len(contents) > 0:
            stored_file = retrieve_file(file.storage_path)
            assert stored_file.read() == contents
        return None


if __name__ == "__main__":
    to_migrate = File.query.filter(File.storage_path.is_(None)).count()
    print("Files to migrate:", to_migrate)

    migrated = 0

    for organization in Organization.query.all():
        print("Org:", organization.name)
        for election in organization.elections:
            print("Election:", election.audit_name)

            if election.jurisdictions_file:
                path = migrate_file(
                    election.jurisdictions_file,
                    f"audits/{election.id}/"
                    + timestamp_filename("participating_jurisdictions", "csv"),
                )
                if path:
                    print("Migrated jurisdictions file to", path)
                    migrated += 1

            if election.standardized_contests_file:
                path = migrate_file(
                    election.standardized_contests_file,
                    f"audits/{election.id}/"
                    + timestamp_filename("standardized_contests", "csv"),
                )
                if path:
                    print("Migrated standardized contests file to", path)
                    migrated += 1

            for jurisdiction in election.jurisdictions:
                print("  Jurisdiction: ", jurisdiction.name)

                if jurisdiction.manifest_file:
                    path = migrate_file(
                        jurisdiction.manifest_file,
                        f"audits/{election.id}/jurisdictions/{jurisdiction.id}/"
                        + timestamp_filename("manifest", "csv"),
                    )
                    if path:
                        print("  Migrated manifest file to", path)
                        migrated += 1

                if jurisdiction.batch_tallies_file:
                    path = migrate_file(
                        jurisdiction.batch_tallies_file,
                        f"audits/{election.id}/jurisdictions/{jurisdiction.id}/"
                        + timestamp_filename("batch_tallies", "csv"),
                    )
                    if path:
                        print("  Migrated batch tallies file to", path)
                        migrated += 1

                if jurisdiction.cvr_file:
                    path = migrate_file(
                        jurisdiction.cvr_file,
                        f"audits/{election.id}/jurisdictions/{jurisdiction.id}/"
                        + timestamp_filename("cvrs", "csv"),
                    )
                    if path:
                        print("  Migrated CVRs file to", path)
                        migrated += 1

            print()
            print(f"Migrated: {migrated}/{to_migrate}")
            db_session.commit()
            print()

    orphans = File.query.filter(File.storage_path.is_(None)).all()
    print("Orphan files:", len(orphans))
    if input("Delete orphan files? (y/n)").lower() == "y":
        for orphan in orphans:
            db_session.delete(orphan)
        db_session.commit()
