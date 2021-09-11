from server.audit_math.raire_utils import *
from server.audit_math.sampler_contest import CVR, CVRS, Contest

from server.audit_math.raire import compute_raire_assertions

import numpy as np

import sys
import argparse

def compare_result(path, contests):
    expected = {}

    with open(path, "r") as exp:
        lines = exp.readlines()

        reading_contest = None

        contest = []
        for line in lines:
            if line.startswith("CONTEST"):
                if reading_contest != None:
                    sorted_contest = sorted(contest)
                    expected[reading_contest] = sorted_contest
                    contest = []

                reading_contest = line.split()[1].strip()
            else:
                contest.append(line.strip())

        expected[reading_contest] = sorted(contest)

    assert len(expected) == len(contests), \
        "Number of contests wrong for {}".format(path)

    for c,asrtns in expected.items():
        assert c in contests, "Incorrect contests for {}".format(path)

        casrtns = contests[c]

        assert len(asrtns) == len(casrtns), \
            print("Number of assertions different for {}, contest {}".format(
                path, c))

        assert asrtns == casrtns, \
            print("Assertions differ for {}, contest {}".format(path,c))


parser = argparse.ArgumentParser()
parser.add_argument('-i', dest='input', required=True)
parser.add_argument('-o', dest='exp_out', required=True)
parser.add_argument('-agap', dest='agap', type=float, default=0)

args = parser.parse_args()

cvr1 = {"test_con" : {"Ann" : 1, "Sally" : 3, "Bob": 2, "Mike" : 4}}

neb1 = NEBAssertion("test_con", "Bob", "Sally")
neb2 = NEBAssertion("test_con", "Ann", "Sally")
neb3 = NEBAssertion("test_con", "Sally", "Bob")

nen1 = NENAssertion("test_con", "Sally", "Ann", ["Bob"])
nen2 = NENAssertion("test_con", "Sally", "Mike", [])
nen3 = NENAssertion("test_con", "Sally", "Mike", ["Bob", "Ann"])

assert(neb1.is_vote_for_winner(cvr1) == 0)
assert(neb1.is_vote_for_loser(cvr1) == 0)
    
assert(neb2.is_vote_for_winner(cvr1) == 1)
assert(neb2.is_vote_for_loser(cvr1) == 0)
    
assert(neb3.is_vote_for_winner(cvr1) == 0)
assert(neb3.is_vote_for_loser(cvr1) == 1)

assert(nen1.is_vote_for_winner(cvr1) == 0)
assert(nen1.is_vote_for_loser(cvr1) == 1)
    
assert(nen2.is_vote_for_winner(cvr1) == 0)
assert(nen2.is_vote_for_loser(cvr1) == 0)
    
assert(nen3.is_vote_for_winner(cvr1) == 1)
assert(nen3.is_vote_for_loser(cvr1) == 0)


                     

# Load test contest
contests = {}
result = {}

with open(args.input, "r") as data:
    lines = data.readlines()

    ncontests = int(lines[0])

    contests = {}
    winners = {}

    for i in range(ncontests):
        toks = lines[1+i].strip().split(',')

        cid = toks[1]
        ncands = int(toks[2])

        # Not sure what votesAllowed is, but RAIRE won't access these 
        # fields of the contest structure anyway.
        cands = {'ballots' : 0, 'numWinners' : 1, 'votesAllowed' : 1}

        for j in range(ncands):
            cands[toks[3+j]] = 0

        contests[cid] = cands
        winners[cid] = toks[-1]

    cvrs = {}

    for l in range(ncontests+1,len(lines)):
        toks = lines[l].strip().split(',')
        
        cid = toks[0]
        bid = toks[1]
        prefs = toks[2:]

        if prefs != []:
            contests[cid][prefs[0]] += 1

        contests[cid]['ballots'] += 1

        ballot = {}
        for c in contests[cid]:
            if c in prefs:
                idx = prefs.index(c) + 1
                ballot[c] = idx
            else:
                ballot[c] = 0

        if not bid in cvrs:
            cvrs[bid] = {cid: ballot}
        else:
            cvrs[bid][cid] = ballot

    for c,votes in contests.items():
        con = Contest(c, votes)
        winner = winners[c]

        audit = compute_raire_assertions(con, cvrs, winners[c], 
            lambda m : 1/m if m > 0 else np.inf, False, agap=args.agap)

        asrtns = []
        for assertion in audit:
            asrtns.append(assertion.to_str())

        sorted_asrtns = sorted(asrtns)
        result[c] = sorted_asrtns

    compare_result(args.exp_out, result)
