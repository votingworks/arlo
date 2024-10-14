# pylint: disable=invalid-name,consider-using-f-string
from typing import List, Dict
import pytest
import numpy as np

from ...audit_math.sampler_contest import Contest
from ...audit_math.raire import (
    NEBMatrix,
    compute_raire_assertions,
    make_neb_matrix,
    make_frontier,
    find_assertions,
)
from ...audit_math.raire_utils import (
    find_best_audit,
    RaireFrontier,
    RaireNode,
    NEBAssertion,
    NENAssertion,
    RaireAssertion,
    CVRS,
)
from .test_raire_utils import make_neb_assertion

RAIRE_INPUT_DIR = "server/tests/audit_math/raire_data/input/"
RAIRE_OUTPUT_DIR = "server/tests/audit_math/raire_data/output/"

BallotList = List[Dict[str, int]]


@pytest.fixture
def contest() -> Contest:
    return Contest(
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
def cvrs() -> CVRS:
    cvrs: CVRS = {}
    for i in range(25000):
        cvrs[f"Ballot {i}"] = {"Contest A": {"winner": 1, "loser": 2, "loser2": 3}}
    for i in range(25000, 50000):
        cvrs[f"Ballot {i}"] = {"Contest A": {"winner": 1, "loser": 3, "loser2": 2}}
    for i in range(50000, 80000):
        cvrs[f"Ballot {i}"] = {"Contest A": {"winner": 2, "loser": 1, "loser2": 3}}
    for i in range(80000, 100000):
        cvrs[f"Ballot {i}"] = {"Contest A": {"winner": 2, "loser": 3, "loser2": 1}}

    return cvrs


@pytest.fixture
def ballots() -> List[Dict[str, int]]:
    ballots = []
    for _ in range(25000):
        ballots.append({"winner": 1, "loser": 2, "loser2": 3})
    for _ in range(25000):
        ballots.append({"winner": 1, "loser": 3, "loser2": 2})
    for _ in range(30000):
        ballots.append({"winner": 2, "loser": 1, "loser2": 3})
    for _ in range(20000):
        ballots.append({"winner": 2, "loser": 3, "loser2": 1})

    return ballots


def asn_func(m):
    return 1 / m if m > 0 else np.inf


def test_make_neb_matrix(contest: Contest, cvrs: CVRS):
    expected: NEBMatrix = {
        c: {
            d: make_neb_assertion(contest, cvrs, asn_func, c, d, set())
            for d in contest.candidates
        }
        for c in contest.candidates
    }

    expected_pairs = [("winner", "loser"), ("winner", "loser2")]
    for cand in expected:
        for other in expected:
            if (cand, other) not in expected_pairs:
                expected[cand][other] = None

    assert make_neb_matrix(contest, cvrs, asn_func) == expected


def test_make_raire_frontier(contest: Contest, cvrs: CVRS, ballots: BallotList):
    nebs = make_neb_matrix(contest, cvrs, asn_func)
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

    assert expected == make_frontier(contest, ballots, nebs, asn_func)


def test_find_assertions_too_good_ancestor(
    contest: Contest, ballots: BallotList, cvrs: CVRS
):

    nebs = make_neb_matrix(contest, cvrs, asn_func)
    frontier = make_frontier(contest, ballots, nebs, asn_func)

    # Create a fake best ancestor
    newn = RaireNode(["loser"])
    newn.expandable = False
    newn.estimate = -100
    newn.best_assertion = frontier.nodes[0].best_assertion

    frontier.nodes[0].best_ancestor = newn

    lowerbound = -10.0

    find_assertions(contest, ballots, nebs, asn_func, frontier, lowerbound, 0)

    # Check that our fake ancestor is the best assertion
    assert frontier.nodes[0].best_assertion == newn.best_assertion

    # Do the same thing, but with an agap and a fake lowerbound
    find_assertions(contest, ballots, nebs, asn_func, frontier, 0.00000001, 0.001)
    assert frontier.nodes[0].best_assertion == newn.best_assertion


def test_find_assertions_infinite_to_expand(
    contest: Contest, ballots: BallotList, cvrs: CVRS
):
    nebs = make_neb_matrix(contest, cvrs, asn_func)
    frontier = make_frontier(contest, ballots, nebs, asn_func)

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


def test_find_assertions_fake_ancestor(
    contest: Contest, ballots: BallotList, cvrs: CVRS
):
    nebs = make_neb_matrix(contest, cvrs, asn_func)
    frontier = make_frontier(contest, ballots, nebs, asn_func)

    lowerbound = -10.0

    # Create a fake best ancestor
    newn = RaireNode(["loser2"])
    # now insert a fake node into the frontier that has infinite cost and
    # make sure the audit can't complete
    newn.estimate = -1
    newn.expandable = True

    frontier.nodes[0].best_ancestor = newn

    assert find_assertions(contest, ballots, nebs, asn_func, frontier, lowerbound, 0)


def test_find_assertions_infinite_branch(
    contest: Contest, ballots: BallotList, cvrs: CVRS
):
    # Fake neb_matrix into showing all assertions but one as infinite
    nebs = make_neb_matrix(contest, cvrs, asn_func)
    nebs["loser"]["winner"] = make_neb_assertion(
        contest, cvrs, asn_func, "loser", "winner", set()
    )
    assert isinstance(nebs["loser"]["winner"], NEBAssertion)
    nebs["loser"]["winner"].difficulty = 0.0000001

    nebs["winner"]["loser2"] = make_neb_assertion(
        contest, cvrs, asn_func, "winner", "loser2", set()
    )
    assert isinstance(nebs["winner"]["loser2"], NEBAssertion)
    nebs["winner"]["loser2"].difficulty = np.inf

    frontier = make_frontier(contest, ballots, nebs, asn_func)

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


def test_find_assertions_many_children(
    contest: Contest, ballots: BallotList, cvrs: CVRS
):
    nebs = make_neb_matrix(contest, cvrs, asn_func)
    frontier = make_frontier(contest, ballots, nebs, asn_func)

    lowerbound = -10.0

    # Create a fake best ancestor
    newn = RaireNode(["loser2"])
    # now insert a fake node into the frontier that has infinite cost and
    # make sure the audit can't complete
    newn.estimate = 0.0006
    newn.expandable = True

    frontier.nodes.insert(0, newn)
    assert find_assertions(contest, ballots, nebs, asn_func, frontier, lowerbound, 0)


def compare_result(path: str, contests: Dict[str, List[str]]):
    expected: Dict[str, List[str]] = {}

    with open(path, "r", encoding="utf8") as exp:
        lines = exp.readlines()

        reading_contest = None

        contest_list: List[str] = []
        for line in lines:
            if line.startswith("CONTEST"):
                if reading_contest:
                    sorted_contest = sorted(contest_list)
                    expected[reading_contest] = sorted_contest
                    contest_list = []

                reading_contest = line.split()[1].strip()
            else:
                contest_list.append(line.strip())

        # For the type checker
        assert isinstance(reading_contest, str)
        expected[reading_contest] = sorted(contest_list)

    assert len(expected) == len(contests), "Number of contests wrong for {}".format(
        path
    )

    for contest, asrtns in expected.items():
        assert contest in contests, "Incorrect contests for {}".format(path)

        casrtns = set(contests[contest])

        assert len(asrtns) == len(
            casrtns
        ), "Number of assertions different for {}, contest {}".format(path, contest)

        parsed_asrtns = set()
        for asrtn in asrtns:
            a_type = asrtn.split(",")[0]
            winner = asrtn.split(",")[2]
            loser = asrtn.split(",")[4]
            eliminated = set(asrtn.split("Eliminated,")[-1].split(","))

            parsed_a: RaireAssertion

            if a_type == "NEB":
                parsed_a = NEBAssertion(contest, winner, loser)
            elif a_type == "NEN":
                parsed_a = NENAssertion(contest, winner, loser, eliminated)
            else:
                raise Exception(f"Unexpected assertion type: {a_type}")

            parsed_asrtns.add(str(parsed_a))

        assert (
            set(parsed_asrtns) == casrtns
        ), "Assertions differ for {}, contest {}".format(path, contest)


def parse_raire_input(input_file: str):
    contests = {}
    winners = {}
    cvrs: CVRS = {}
    # Load test contest
    with open(input_file, "r", encoding="utf8") as data:
        lines = data.readlines()

        ncontests = int(lines[0])

        for i in range(ncontests):
            toks = lines[1 + i].strip().split(",")

            cid: str = toks[1]
            ncands: int = int(toks[2])

            # Initialize the contest object with dummy info for now
            cands = {"ballots": 0, "numWinners": 1, "votesAllowed": 1}

            for j in range(ncands):
                cands[toks[3 + j]] = 0

            contests[cid] = cands
            winners[cid] = toks[-1]

        for line in range(ncontests + 1, len(lines)):
            toks = lines[line].strip().split(",")

            cid = toks[0]
            bid: str = toks[1]
            prefs: List[str] = toks[2:]

            if prefs not in [[], [""]]:
                contests[cid][prefs[0]] += 1

            contests[cid]["ballots"] += 1

            ballot: Dict[str, int] = {}
            for cand in contests[cid]:
                if cand in prefs:
                    idx = prefs.index(cand) + 1
                    ballot[cand] = idx
                else:
                    ballot[cand] = 0

            if bid in cvrs:
                cvr = cvrs[bid]
                assert cvr is not None
                cvr[cid] = ballot
            else:
                cvrs[bid] = {cid: ballot}

    return contests, cvrs, winners


def run_test(input_file: str, output_file: str, agap: float):
    result: Dict[str, List[str]] = {}

    contests, cvrs, winners = parse_raire_input(input_file)

    for contest, votes in contests.items():
        con = Contest(contest, votes)
        # Override contest's winners since it's computed only using the first round results
        real_winners = {}
        real_winners[winners[contest]] = con.candidates[winners[contest]]
        con.winners = real_winners

        audit: List[RaireAssertion] = compute_raire_assertions(
            con,
            cvrs,
            lambda m: 1 / m if m > 0 else np.inf,
            agap,
        )

        asrtns: List[str] = [str(assertion) for assertion in audit]
        sorted_asrtns = sorted(asrtns)
        result[contest] = sorted_asrtns

    compare_result(output_file, result)


def test_raire(contest: Contest, cvrs: CVRS):
    res = compute_raire_assertions(contest, cvrs, asn_func)

    expected = []

    # we expect to show that winner is not eliminated before loser2
    expected.append(
        make_neb_assertion(contest, cvrs, asn_func, "winner", "loser2", set([]))
    )

    # we then expect to show that the winner is not eliminated before loser
    expected.append(
        make_neb_assertion(contest, cvrs, asn_func, "winner", "loser", set(["loser2"]))
    )

    # sort by difficulty
    expected = sorted(expected)

    assert res == expected

    # Use a small agap

    res = compute_raire_assertions(contest, cvrs, asn_func, agap=0.00000001)
    assert res == expected


def test_raire_recount():
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

    cvrs = {}
    for i in range(50000):
        cvrs[i] = {"Contest A": {"winner": 1, "loser": 2}}
    for i in range(50000, 100000):
        cvrs[i] = {"Contest A": {"winner": 2, "loser": 1}}

    res = compute_raire_assertions(contest, cvrs, asn_func)

    assert res == []


@pytest.mark.skip("Makes test coverage very slow")
def test_aspen_wrong_winner():
    input_file = RAIRE_INPUT_DIR + "SpecialCases/Aspen_2009_wrong_winner.raire"
    output_file = RAIRE_OUTPUT_DIR + "SpecialCases/Aspen_2009_wrong_winner.raire.out"
    agap = 0
    run_test(input_file, output_file, agap)


def test_berkeley_2010():
    input_file = RAIRE_INPUT_DIR + "Berkeley_2010.raire"
    output_file = RAIRE_OUTPUT_DIR + "Berkeley_2010.raire.out"
    agap = 0
    run_test(input_file, output_file, agap)
