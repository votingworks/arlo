import time

from arlo_server import db
from arlo_server.models import Election, File, Jurisdiction, RoundContest
from arlo_server.routes import compute_sample_sizes
from arlo_server.ballot_manifest import process_ballot_manifest_file
from util.jurisdiction_bulk_update import process_jurisdictions_file

from sqlalchemy.exc import SQLAlchemyError


def bgcompute():
    bgcompute_compute_round_contests_sample_sizes()
    bgcompute_update_election_jurisdictions_file()
    bgcompute_update_ballot_manifest_file()


def bgcompute_compute_round_contests_sample_sizes():
    # round contests that don't have sample_size_options
    round_contests = RoundContest.query.filter_by(sample_size_options=None)

    for round_contest in round_contests:
        try:
            print(
                "computing sample size options for round {:d} of election ID {:s}".format(
                    round_contest.round.round_num, round_contest.round.election_id
                )
            )

            compute_sample_sizes(round_contest)

            print(
                "done computing sample size options for round {:d} of election ID {:s}: {:s}".format(
                    round_contest.round.round_num,
                    round_contest.round.election_id,
                    round_contest.sample_size_options,
                )
            )
        except:
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
            process_jurisdictions_file(db.session, election, file)
            print(f"done updating jurisdictions file for election ID {election.id}")
        except:
            print("ERROR whie updating jurisdictions file")

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
            process_ballot_manifest_file(db.session, jurisdiction, file)
        except SQLAlchemyError as e:
            raise e
        except:
            print("ERROR updating ballot manifest file")

    return len(files)


def bgcompute_forever():
    while True:
        bgcompute()
        time.sleep(2)


if __name__ == "__main__":
    bgcompute_forever()
