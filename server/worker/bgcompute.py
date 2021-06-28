import time

from server.app import app
from server.database import db_session
from server.models import *  # pylint: disable=wildcard-import
from server.util.jurisdiction_bulk_update import process_jurisdictions_file
from server.api.standardized_contests import process_standardized_contests_file
from server.api.ballot_manifest import process_ballot_manifest_file
from server.api.batch_tallies import process_batch_tallies_file
from server.api.cvrs import process_cvr_file
from server.worker.tasks import run_new_tasks
from server.sentry import configure_sentry


def bgcompute():
    bgcompute_update_election_jurisdictions_file()
    bgcompute_update_standardized_contests_file()
    bgcompute_update_ballot_manifest_file()
    bgcompute_update_batch_tallies_file()
    bgcompute_update_cvr_file()


# All bgcompute functions take an optional election_id parameter in order to
# make them thread-safe for testing. Each test has its own election, and we
# don't want tests running in parallel to influence each other.


def bgcompute_update_election_jurisdictions_file(election_id: str = None):
    files = File.query.join(Election, File.id == Election.jurisdictions_file_id).filter(
        File.processing_started_at.is_(None)
    )
    if election_id:
        files = files.filter(Election.id == election_id)

    for file in files.all():
        try:
            election = Election.query.filter_by(jurisdictions_file_id=file.id).one()

            # Save election_id in a variable so we can log it even if some
            # error happens and the election object is borked
            election_id = election.id

            app.logger.info(
                f"START updating jurisdictions file. election_id: {election_id}"
            )

            process_jurisdictions_file(db_session, election, file)

            app.logger.info(
                f"DONE updating jurisdictions file. election_id: {election_id}"
            )
        except Exception:
            app.logger.exception(
                f"ERROR updating jurisdictions file. election_id: {election_id}"
            )

        db_session.commit()


def bgcompute_update_standardized_contests_file(election_id: str = None):
    files = File.query.join(
        Election, File.id == Election.standardized_contests_file_id
    ).filter(File.processing_started_at.is_(None))
    if election_id:
        files = files.filter(Election.id == election_id)

    for file in files.all():
        try:
            election = Election.query.filter_by(
                standardized_contests_file_id=file.id
            ).one()

            # Save election_id in a variable so we can log it even if some
            # error happens and the election object is borked
            election_id = election.id

            app.logger.info(
                f"START updating standardized contests file. election_id: {election_id}"
            )

            process_standardized_contests_file(db_session, election, file)

            app.logger.info(
                f"DONE updating standardized contests file. election_id: {election_id}"
            )
        except Exception:
            app.logger.exception(
                f"ERROR updating standardized contests file. election_id: {election_id}"
            )

        db_session.commit()


def bgcompute_update_ballot_manifest_file(election_id: str = None):
    files = File.query.join(
        Jurisdiction, File.id == Jurisdiction.manifest_file_id
    ).filter(File.processing_started_at.is_(None))
    if election_id:
        files = files.filter(Jurisdiction.election_id == election_id)

    for file in files.all():
        try:
            jurisdiction = Jurisdiction.query.filter_by(manifest_file_id=file.id).one()

            # Save ids in variables so we can log them even if some
            # error happens and the ORM objects are borked
            election_id = jurisdiction.election_id
            jurisdiction_id = jurisdiction.id

            app.logger.info(
                f"START updating ballot manifest file. election_id: {election_id}, jurisdiction_id: {jurisdiction_id}"
            )

            process_ballot_manifest_file(db_session, jurisdiction, file)

            app.logger.info(
                f"DONE updating ballot manifest file. election_id: {election_id}, jurisdiction_id: {jurisdiction_id}"
            )
        except Exception:
            app.logger.exception(
                f"ERROR updating ballot manifest file. election_id: {election_id}, jurisdiction_id: {jurisdiction_id}"
            )

        db_session.commit()


def bgcompute_update_batch_tallies_file(election_id: str = None):
    files = File.query.join(
        Jurisdiction, File.id == Jurisdiction.batch_tallies_file_id
    ).filter(File.processing_started_at.is_(None))
    if election_id:
        files = files.filter(Jurisdiction.election_id == election_id)

    for file in files.all():
        try:
            jurisdiction = Jurisdiction.query.filter_by(
                batch_tallies_file_id=file.id
            ).one()

            # Save ids in variables so we can log them even if some
            # error happens and the ORM objects are borked
            election_id = jurisdiction.election_id
            jurisdiction_id = jurisdiction.id

            app.logger.info(
                f"START updating batch tallies file. election_id: {election_id}, jurisdiction_id: {jurisdiction_id}"
            )

            process_batch_tallies_file(db_session, jurisdiction, file)

            app.logger.info(
                f"DONE updating batch tallies file. election_id: {election_id}, jurisdiction_id: {jurisdiction_id}"
            )
        except Exception:
            app.logger.exception(
                f"ERROR updating batch tallies file. election_id: {election_id}, jurisdiction_id: {jurisdiction_id}"
            )

        db_session.commit()


def bgcompute_update_cvr_file(election_id: str = None):
    files = File.query.join(Jurisdiction, File.id == Jurisdiction.cvr_file_id).filter(
        File.processing_started_at.is_(None)
    )
    if election_id:
        files = files.filter(Jurisdiction.election_id == election_id)

    for file in files.all():
        try:
            jurisdiction = Jurisdiction.query.filter_by(cvr_file_id=file.id).one()

            # Save ids in variables so we can log them even if some
            # error happens and the ORM objects are borked
            election_id = jurisdiction.election_id
            jurisdiction_id = jurisdiction.id

            app.logger.info(
                f"START updating CVR file. election_id: {election_id}, jurisdiction_id: {jurisdiction_id}"
            )

            process_cvr_file(db_session, jurisdiction, file)

            app.logger.info(
                f"DONE updating CVR file. election_id: {election_id}, jurisdiction_id: {jurisdiction_id}"
            )
        except Exception:
            app.logger.exception(
                f"ERROR updating CVR file. election_id: {election_id}, jurisdiction_id: {jurisdiction_id}"
            )

        db_session.commit()


def bgcompute_forever():
    while True:
        bgcompute()
        run_new_tasks()
        # Before sleeping, we need to commit the curren transaction, otherwise
        # we will have "idle in transaction" queries that will lock the
        # database, which gets in the way of migrations.
        db_session.commit()
        time.sleep(2)


if __name__ == "__main__":
    configure_sentry()
    bgcompute_forever()
