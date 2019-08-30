
import time, json

from flask import Flask

from app import app, db, compute_and_store_sample_sizes
from models import Election, TargetedContest

def bgcompute():
    # elections that have contests but no sample size
    query = db.session.query(TargetedContest.election_id).group_by(TargetedContest.election_id).join(Election).filter(Election.sample_size_options.is_(None))
    election_ids = [e[0] for e in query.all()]

    for election_id in election_ids:
        print("computing sample size options for election ID {:s}".format(election_id))
        election = Election.query.filter_by(id = election_id).one()
        election.sample_size_options = json.dumps(compute_and_store_sample_sizes(election))
        db.session.commit()
        print("done computing sample size options for election ID {:s}".format(election_id))

def bgcompute_forever():
    while True:
        bgcompute()
        time.sleep(2)
        
if __name__=="__main__":
    bgcompute_forever()
