import numpy as np
import pytest
from itertools import product
from typing import Generator, List

from server.audit_math.sampler_contest import Contest, CVR
from server.audit_math.raire import (
    NEBMatrix,
    compute_raire_assertions,
    make_neb_matrix,
    make_frontier,
    find_assertions,
)
from server.audit_math.raire_utils import (
    NEBAssertion,
    NENAssertion,
    find_best_audit,
    RaireFrontier,
    RaireNode,
)
from server.tests.audit_math.test_raire_utils import (
    make_nen_assertion,
    make_neb_assertion,
)

RAIRE_INPUT_DIR = "server/tests/audit_math/RaireData/Input/"
RAIRE_OUTPUT_DIR = "server/tests/audit_math/RaireData/Output/"


@pytest.fixture
def contest() -> Generator[Contest, None, None]:
    yield Contest(
        "Contest A",
        {
            "winner": 50000,
            "loser": 30000,
            "loser2": 20000,
            "ballots": 100000,
            "numWinners": 1,
            "votesAllowed": 1,
        },
    )

@pytest.fixture
def ballots() -> Generator[List[CVR], None, None]:
    ballots = []
    for _ in range(25000):
        ballots.append({"Contest A": {"winner": 1, "loser": 2, "loser2": 3}})
    for _ in range(25000):
        ballots.append({"Contest A": {"winner": 1, "loser": 3, "loser2": 2}})
    for _ in range(30000):
        ballots.append({"Contest A": {"winner": 2, "loser": 1, "loser2": 3}})
    for _ in range(20000):
        ballots.append({"Contest A": {"winner": 2, "loser": 3, "loser2": 1}})

    yield ballots

# TODO does this really need to be a fixture?
@pytest.fixture
def asn_func():
    yield lambda m: 1 / m if m > 0 else np.inf


def test_make_neb_matrix(contest, ballots, asn_func):
    expected: NEBMatrix = {
        c: {
            d: make_neb_assertion(contest, ballots, asn_func, c, d, [])
            for d in contest.candidates
        }
        for c in contest.candidates
    }

    expected_pairs = [("winner", "loser"), ("winner", "loser2")]
    for cand in expected:
        for other in expected:
            if (cand, other) not in expected_pairs:
                expected[cand][other] = None

    assert make_neb_matrix(contest, ballots, asn_func) == expected


def test_make_raire_frontier(contest, ballots, asn_func):
    nebs = make_neb_matrix(contest, ballots, asn_func)
    expected = RaireFrontier()

    # enumerate all possible nodes
    pairs = [
        ("loser", "loser2"),
        ("loser2", "loser"),
        ("winner", "loser"),
        ("winner", "loser2"),
    ]

    for other, cand in pairs:
        node = RaireNode([other, cand])
        node.expandable = True
        find_best_audit(contest, ballots, nebs, node, asn_func)
        expected.insert_node(node)

    assert expected == make_frontier(contest, ballots, "winner", nebs, asn_func)


def test_find_assertions_too_good_ancestor(contest, ballots, asn_func):

    nebs = make_neb_matrix(contest, ballots, asn_func)
    frontier = make_frontier(contest, ballots, "winner", nebs, asn_func)

    # Create a fake best ancestor
    newn = RaireNode(["loser"])
    newn.expandable = False
    newn.estimate = -100
    newn.best_assertion = frontier.nodes[0].best_assertion

    frontier.nodes[0].best_ancestor = newn

    lowerbound = -10.0

    find_assertions(contest, ballots, nebs, asn_func, frontier, lowerbound, 0)

    # Check that our fake ancestor is the best assertiont
    assert frontier.nodes[0].best_assertion == newn.best_assertion

    # Do the same thing, but with an agap and a fake lowerbound
    find_assertions(contest, ballots, nebs, asn_func, frontier, 0.00000001, 0.001)
    assert frontier.nodes[0].best_assertion == newn.best_assertion


def test_find_assertions_infinite_to_expand(contest, ballots, asn_func):
    nebs = make_neb_matrix(contest, ballots, asn_func)
    frontier = make_frontier(contest, ballots, "winner", nebs, asn_func)

    lowerbound = -10.0

    # Create a fake best ancestor
    newn = RaireNode(["winner", "loser"])
    # now insert a fake node into the frontier that has infinite cost and
    # make sure the audit can't complete
    newn.estimate = np.inf
    newn.expandable = True

    frontier.nodes.insert(0, newn)

    assert not find_assertions(
        contest, ballots, nebs, asn_func, frontier, lowerbound, 0
    )


def test_find_assertions_fake_ancestor(contest, ballots, asn_func):
    nebs = make_neb_matrix(contest, ballots, asn_func)
    frontier = make_frontier(contest, ballots, "winner", nebs, asn_func)

    lowerbound = -10.0

    # Create a fake best ancestor
    newn = RaireNode(["loser2"])
    # now insert a fake node into the frontier that has infinite cost and
    # make sure the audit can't complete
    newn.estimate = -1
    newn.expandable = True

    frontier.nodes[0].best_ancestor = newn

    assert find_assertions(contest, ballots, nebs, asn_func, frontier, lowerbound, 0)


def test_find_assertions_infinite_branch(contest, ballots, asn_func):
    # Fake neb_matrix into showing all assertions but one as infinite
    nebs = make_neb_matrix(contest, ballots, asn_func)
    nebs["loser"]["winner"] = make_neb_assertion(
        contest, ballots, asn_func, "loser", "winner", []
    )
    nebs["loser"]["winner"].difficulty = 0.0000001

    nebs["winner"]["loser2"] = make_neb_assertion(
        contest, ballots, asn_func, "winner", "loser2", []
    )
    nebs["winner"]["loser2"].difficulty = np.inf

    frontier = make_frontier(contest, ballots, "winner", nebs, asn_func)

    lowerbound = -10.0

    # Create a fake best ancestor
    newn = RaireNode(["winner", "winner"])
    # now insert a fake node into the frontier that has infinite cost and
    # make sure the audit can't complete
    newn.estimate = np.inf
    newn.expandable = True

    frontier.nodes.insert(0, newn)

    assert not find_assertions(
        contest, ballots, nebs, asn_func, frontier, lowerbound, 0
    )


def test_find_assertions_many_children(contest, ballots, asn_func):
    nebs = make_neb_matrix(contest, ballots, asn_func)
    frontier = make_frontier(contest, ballots, "winner", nebs, asn_func)

    lowerbound = -10.0

    # Create a fake best ancestor
    newn = RaireNode(["loser2"])
    # now insert a fake node into the frontier that has infinite cost and
    # make sure the audit can't complete
    newn.estimate = 0.0006
    newn.expandable = True

    frontier.nodes.insert(0, newn)
    assert find_assertions(contest, ballots, nebs, asn_func, frontier, lowerbound, 0)


def compare_result(path, contests):
    expected = {}

    with open(path, "r") as exp:
        lines = exp.readlines()

        reading_contest = None

        contest = []
        for line in lines:
            if line.startswith("CONTEST"):
                if reading_contest:
                    sorted_contest = sorted(contest)
                    expected[reading_contest] = sorted_contest
                    contest = []

                reading_contest = line.split()[1].strip()
            else:
                contest.append(line.strip())

        expected[reading_contest] = sorted(contest)

    assert len(expected) == len(contests), "Number of contests wrong for {}".format(
        path
    )

    for contest, asrtns in expected.items():
        assert contest in contests, "Incorrect contests for {}".format(path)

        casrtns = contests[contest]

        assert len(asrtns) == len(casrtns), print(
            "Number of assertions different for {}, contest {}".format(path, contest)
        )

        assert asrtns == casrtns, print(
            "Assertions differ for {}, contest {}".format(path, contest)
        )


def run_test(input_file, output_file, agap):
    result = {}
    # Load test contest
    with open(input_file, "r") as data:
        lines = data.readlines()

        ncontests = int(lines[0])

        contests = {}
        winners = {}

        for i in range(ncontests):
            toks = lines[1 + i].strip().split(",")

            cid = toks[1]
            ncands = int(toks[2])

            # Not sure what votesAllowed is, but RAIRE won't access these
            # fields of the contest structure anyway.
            cands = {"ballots": 0, "numWinners": 1, "votesAllowed": 1}

            for j in range(ncands):
                cands[toks[3 + j]] = 0

            contests[cid] = cands
            winners[cid] = toks[-1]

        cvrs = {}

        for l in range(ncontests + 1, len(lines)):
            toks = lines[l].strip().split(",")

            cid = toks[0]
            bid = toks[1]
            prefs = toks[2:]

            if prefs != []:
                contests[cid][prefs[0]] += 1

            contests[cid]["ballots"] += 1

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

        for contest, votes in contests.items():
            con = Contest(contest, votes)


            audit = compute_raire_assertions(
                con,
                cvrs,
                winners[contest],
                lambda m: 1 / m if m > 0 else np.inf,
                agap,
            )

            asrtns = []
            for assertion in audit:
                asrtns.append(str(assertion))

            sorted_asrtns = sorted(asrtns)
            result[contest] = sorted_asrtns

        compare_result(output_file, result)


def test_raire(contest, ballots, asn_func):
    res = compute_raire_assertions(contest, ballots, "winner", asn_func)

    expected = []

    # we expect to show that winner is not eliminated before loser2
    expected.append(
        make_neb_assertion(contest, ballots, asn_func, "winner", "loser2", [])
    )

    # we expect loser to be eliminated next
    expected.append(
        make_nen_assertion(contest, ballots, asn_func, "winner", "loser", ["loser2"])
    )

    # sort by difficuly
    expected = sorted(expected)

    assert res == expected

    # Use a small agap

    res = compute_raire_assertions(
        contest, ballots, "winner", asn_func, agap=0.00000001
    )
    assert res == expected


def test_raire_recount(asn_func):
    contest = Contest(
        "Contest A",
        {
            "winner": 50000,
            "loser": 50000,
            "ballots": 100000,
            "numWinners": 1,
            "votesAllowed": 1,
        },
    )

    ballots = []
    for _ in range(50000):
        ballots.append({"Contest A": {"winner": 1, "loser": 2}})
    for _ in range(50000):
        ballots.append({"Contest A": {"winner": 2, "loser": 1}})

    res = compute_raire_assertions(contest, ballots, "winner", asn_func)

    # assert res == []


def test_aspen_wrong_winner():
    input_file = RAIRE_INPUT_DIR + "SpecialCases/Aspen_2009_wrong_winner.raire"
    output_file = RAIRE_OUTPUT_DIR + "SpecialCases/Aspen_2009_wrong_winner.raire.out"
    agap = 0
    run_test(input_file, output_file, agap)


def test_berkeley_2010():
    input_file = RAIRE_INPUT_DIR + "Berkeley_2010.raire"
    output_file = RAIRE_OUTPUT_DIR + "Berkeley_2010.raire.out"
    agap = 0.00001
    run_test(input_file, output_file, agap)
