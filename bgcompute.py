# type: ignore
import time, json

from flask import Flask

from arlo_server import app, db
from arlo_server.models import RoundContest
from arlo_server.routes import compute_sample_sizes


def bgcompute():
    # round contests that don't have sample_size_options
    round_contests = RoundContest.query.filter_by(sample_size_options=None)

    for round_contest in round_contests:
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


def bgcompute_forever():
    while True:
        bgcompute()
        time.sleep(2)


if __name__ == "__main__":
    bgcompute_forever()
