# type: ignore
import time, json

from flask import Flask

from app import app, db, compute_sample_sizes
from models import RoundContest

def bgcompute():
    # round contests that don't have sample_size_options
    round_contests = RoundContest.query.filter_by(sample_size_options = None)

    for round_contest in round_contests:
        print("computing sample size options for round {:d} of election ID {:s}".format(round_contest.round.round_num, round_contest.round.election_id))

        compute_sample_sizes(round_contest)

        print("done computing sample size options for round {:d} of election ID {:s}: {:s}".format(round_contest.round.round_num, round_contest.round.election_id, round_contest.sample_size_options))


def bgcompute_forever():
    while True:
        bgcompute()
        time.sleep(2)
        
if __name__=="__main__":
    bgcompute_forever()
