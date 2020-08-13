import time
from sqlalchemy import update

from server.database import db_session
from server.models import *  # pylint: disable=wildcard-import
from server.api.routes import compute_sample_sizes
from server.api.ballot_manifest import process_ballot_manifest_file
from server.api.batch_tallies import process_batch_tallies_file
from server.util.jurisdiction_bulk_update import process_jurisdictions_file


def bgcompute():
    bgcompute_compute_round_contests_sample_sizes()
    bgcompute_update_election_jurisdictions_file()
    bgcompute_update_ballot_manifest_file()
    bgcompute_update_batch_tallies_file()


def bgcompute_compute_round_contests_sample_sizes():
    # Round contests that don't have sample_size_options - only in single-jurisdiction audits
    # Multi-jurisdiction audits compute estimated sample sizes on demand
    round_contests = (
        RoundContest.query.filter_by(sample_size_options=None)
        .join(Round)
        .join(Election)
        .filter_by(is_multi_jurisdiction=False)
        .all()
    )

    for round_contest in round_contests:
        try:
            print(
                "computing sample size options for round {:d} of election ID {:s}".format(
                    round_contest.round.round_num, round_contest.round.election_id
                )
            )

            # Claim this RoundContest by updating the sample_size_options field
            # to an "in progress" value This acts like a lock on the
            # RoundContest so it can only get processed once (since this
            # process has a side effect of sampling ballots in some cases,
            # which we only want to happen once).
            result = db_session.execute(
                update(RoundContest.__table__)  # pylint: disable=no-member
                .where(RoundContest.contest_id == round_contest.contest_id)
                .where(RoundContest.round_id == round_contest.round_id)
                .where(RoundContest.sample_size_options.is_(None))
                .values(sample_size_options="CALCULATION_IN_PROGRESS")
            )
            if result.rowcount == 0:
                continue

            compute_sample_sizes(round_contest)

            print(
                "done computing sample size options for round {:d} of election ID {:s}: {:s}".format(
                    round_contest.round.round_num,
                    round_contest.round.election_id,
                    round_contest.sample_size_options,
                )
            )
        except Exception:
            print("ERROR while computing sample size options, continuing to next one.")


def bgcompute_update_election_jurisdictions_file() -> int:
    files = (
        File.query.join(Election, File.id == Election.jurisdictions_file_id)
        .filter(File.processing_started_at.is_(None))
        .all()
    )

    for file in files:
        try:
            election = Election.query.filter_by(jurisdictions_file_id=file.id).one()
            print(f"updating jurisdictions file for election ID {election.id}")
            process_jurisdictions_file(db_session, election, file)
            print(f"done updating jurisdictions file for election ID {election.id}")
        except Exception:
            print("ERROR while updating jurisdictions file")

    return len(files)


def bgcompute_update_ballot_manifest_file() -> int:
    files = (
        File.query.join(Jurisdiction, File.id == Jurisdiction.manifest_file_id)
        .filter(File.processing_started_at.is_(None))
        .all()
    )

    for file in files:
        try:
            jurisdiction = Jurisdiction.query.filter_by(manifest_file_id=file.id).one()
            process_ballot_manifest_file(db_session, jurisdiction, file)
        except Exception:
            print("ERROR updating ballot manifest file")

    return len(files)


def bgcompute_update_batch_tallies_file() -> int:
    files = (
        File.query.join(Jurisdiction, File.id == Jurisdiction.batch_tallies_file_id)
        .filter(File.processing_started_at.is_(None))
        .all()
    )

    for file in files:
        try:
            jurisdiction = Jurisdiction.query.filter_by(
                batch_tallies_file_id=file.id
            ).one()
            process_batch_tallies_file(db_session, jurisdiction, file)
        except Exception:
            print("ERROR updating batch tallies file")

    return len(files)


def bgcompute_forever():
    while True:
        bgcompute()
        time.sleep(2)


if __name__ == "__main__":
    bgcompute_forever()
