from typing import List, Dict, Callable, Set
import pytest
import numpy as np

from ...audit_math.sampler_contest import Contest
from ...audit_math import raire_utils
from ...audit_math.raire_utils import NEBAssertion, NENAssertion, CVRS

# TODO: update this type def
AsnFunc = Callable


def test_ranking_not_on_ballots():
    cand = "not on ballot"
    ballot: Dict[str, int] = {
        "A": 1,
        "B": 2,
        "C": 3,
    }

    assert raire_utils.ranking(cand, ballot) == 0


def test_ranking():
    ballot: Dict[str, int] = {
        "A": 1,
        "B": 2,
        "C": 3,
        "D": 0,
    }

    assert raire_utils.ranking("A", ballot) == 1
    assert raire_utils.ranking("B", ballot) == 2
    assert raire_utils.ranking("C", ballot) == 3
    assert raire_utils.ranking("D", ballot) == 0
    assert raire_utils.ranking("E", ballot) == 0


def test_vote_for_candidate():
    ballot: Dict[str, int] = {
        "A": 1,
        "B": 2,
        "C": 3,
        "D": 0,
    }

    assert raire_utils.vote_for_cand("A", [], ballot)
    assert not raire_utils.vote_for_cand("B", [], ballot)
    assert raire_utils.vote_for_cand("B", ["A"], ballot)
    assert not raire_utils.vote_for_cand("D", [], ballot)


def test_vote_for_eliminated_cand():
    cand = "C"
    ballot: Dict[str, int] = {
        "A": 1,
        "B": 2,
        "C": 3,
    }
    eliminated = ["C"]
    assert raire_utils.vote_for_cand(cand, eliminated, ballot) == 0


def test_raire_assertion_comparator():
    contest = Contest(
        "Contest A",
        {
            "winner": 60000,
            "loser": 40000,
            "ballots": 100000,
            "numWinners": 1,
            "votesAllowed": 1,
        },
    )

    asrtn_1 = raire_utils.RaireAssertion(contest, "winner", "loser")
    asrtn_2 = raire_utils.RaireAssertion(contest, "winner", "loser")

    # Counter-intuitively, assertions with smaller difficulties are "greater"
    asrtn_1.difficulty = 6
    asrtn_2.difficulty = 5
    assert (
        asrtn_2 > asrtn_1
    ), f"__gt__ failed! {asrtn_1.difficulty} {asrtn_2.difficulty}"
    assert (
        asrtn_1 < asrtn_2
    ), f"__lt__ failed! {asrtn_1.difficulty} {asrtn_2.difficulty}"


def test_raire_assertion_to_str():
    contest = Contest(
        "Contest A",
        {
            "winner": 60000,
            "loser": 40000,
            "ballots": 100000,
            "numWinners": 1,
            "votesAllowed": 1,
        },
    )

    expected = str(contest) + " winner loser inf"
    asrtn_1 = raire_utils.RaireAssertion(contest, "winner", "loser")
    assert str(asrtn_1) == expected


def test_nebassertion():
    contest = "Contest A"

    asrtn_1 = raire_utils.NEBAssertion(contest, "winner", "loser")
    cvr = {}

    assert asrtn_1.is_vote_for_winner(cvr) == 0
    assert asrtn_1.is_vote_for_loser(cvr) == 0

    cvr = {contest: {"winner": 1, "loser": 2}}
    assert asrtn_1.is_vote_for_winner(cvr) == 1
    assert asrtn_1.is_vote_for_loser(cvr) == 0

    # pylint: disable=comparison-with-itself
    assert asrtn_1 == asrtn_1

    cvr = {"Contest B": {"winner": 1, "loser": 2}}
    assert not asrtn_1.is_vote_for_winner(cvr)
    assert not asrtn_1.is_vote_for_loser(cvr)

    # checking hashability
    assert list(set([asrtn_1])) == [asrtn_1]


def test_simple_contest():
    cvr1 = {"test_con": {"Ann": 1, "Sally": 3, "Bob": 2, "Mike": 4}}

    neb1 = raire_utils.NEBAssertion("test_con", "Bob", "Sally")
    neb2 = raire_utils.NEBAssertion("test_con", "Ann", "Sally")
    neb3 = raire_utils.NEBAssertion("test_con", "Sally", "Bob")

    nen1 = raire_utils.NENAssertion("test_con", "Sally", "Ann", ["Bob"])
    nen2 = raire_utils.NENAssertion("test_con", "Sally", "Mike", [])
    nen3 = raire_utils.NENAssertion("test_con", "Sally", "Mike", ["Bob", "Ann"])

    assert neb1.is_vote_for_winner(cvr1) == 0
    assert neb1.is_vote_for_loser(cvr1) == 0

    assert neb2.is_vote_for_winner(cvr1) == 1
    assert neb2.is_vote_for_loser(cvr1) == 0

    assert neb3.is_vote_for_winner(cvr1) == 0
    assert neb3.is_vote_for_loser(cvr1) == 1

    assert nen1.is_vote_for_winner(cvr1) == 0
    assert nen1.is_vote_for_loser(cvr1) == 1

    assert nen2.is_vote_for_winner(cvr1) == 0
    assert nen2.is_vote_for_loser(cvr1) == 0

    assert nen3.is_vote_for_winner(cvr1) == 1
    assert nen3.is_vote_for_loser(cvr1) == 0


def test_nebassertion_subsumes():
    contest = "Contest A"

    asrtn_1 = raire_utils.NEBAssertion(contest, "winner", "loser")
    asrtn_2 = raire_utils.NEBAssertion(contest, "winner", "loser")
    asrtn_3 = raire_utils.NENAssertion(contest, "winner", "loser", [])

    assert not asrtn_1.subsumes(asrtn_2)
    assert not asrtn_2.subsumes(asrtn_1)

    # NEB subsumes NEN
    assert asrtn_1.subsumes(asrtn_3)
    # But not the other way around
    assert not asrtn_3.subsumes(asrtn_1)

    asrtn_3.winner = "loser"
    asrtn_3.loser = "winner"
    asrtn_3.rules_out = ["winner", "loser"]
    assert asrtn_1.subsumes(asrtn_3)

    asrtn_3.rules_out = []
    assert not asrtn_1.subsumes(asrtn_3)


def test_neb_repr():
    asrtn_1 = raire_utils.NEBAssertion("Contest A", "winner", "loser")

    expected = "NEB,Winner,winner,Loser,loser,Eliminated"
    assert str(asrtn_1) == expected


def test_nenassertion_is_vote_for():
    contest = "Contest A"
    asrtn_1 = raire_utils.NENAssertion(contest, "winner", "loser", [])
    cvr = {}

    assert asrtn_1.is_vote_for_winner(cvr) == 0
    assert asrtn_1.is_vote_for_loser(cvr) == 0

    cvr = {"Contest A": {"winner": 1, "loser": 2}}
    assert asrtn_1.is_vote_for_winner(cvr) == 1
    assert asrtn_1.is_vote_for_loser(cvr) == 0

    # pylint: disable=comparison-with-itself
    assert asrtn_1 == asrtn_1

    cvr = {"Contest B": {"winner": 1, "loser": 2}}
    assert not asrtn_1.is_vote_for_winner(cvr)
    assert not asrtn_1.is_vote_for_loser(cvr)


def test_nenassertion_subsumes():
    contest = "Contest A"

    asrtn_1 = raire_utils.NENAssertion(contest, "winner", "loser", [])
    asrtn_2 = raire_utils.NENAssertion(contest, "winner", "loser", [])

    # These should both subsume each other
    assert asrtn_1.subsumes(asrtn_2) == 1
    assert asrtn_2.subsumes(asrtn_1) == 1

    asrtn_2.winner = "loser"
    asrtn_2.loser = "winner"
    assert not asrtn_1.subsumes(asrtn_2)


def test_nen_repr():
    expected = "NEN,Winner,winner,Loser,loser,Eliminated,"
    asrtn_1 = raire_utils.NENAssertion("Contest A", "winner", "loser", [])
    assert str(asrtn_1) == expected


def test_nen_hash():
    asrtn_1 = raire_utils.NENAssertion("Contest A", "winner", "loser", [])
    # checking hashability
    assert list(set([asrtn_1])) == [asrtn_1]


def test_raire_node_descendents():

    parent = raire_utils.RaireNode(["b", "a"])
    not_child = raire_utils.RaireNode(["c", "a"])

    # These are two unrelated nodes
    assert not not_child.is_descendent_of(parent)
    assert not parent.is_descendent_of(not_child)

    child = raire_utils.RaireNode(["c", "b", "a"])
    assert child.is_descendent_of(parent)
    assert not child.is_descendent_of(not_child)

    assert child != parent
    other = raire_utils.RaireNode(["b", "a"])
    assert other == parent


def test_raire_node_repr():
    node = raire_utils.RaireNode(["c", "b", "a"])
    node.estimate = 5

    contest = Contest(
        "Contest A",
        {
            "winner": 60000,
            "loser": 40000,
            "ballots": 100000,
            "numWinners": 1,
            "votesAllowed": 1,
        },
    )
    best_assertion = raire_utils.RaireAssertion(contest, "winner", "loser")
    node.best_assertion = best_assertion

    expected = f"tail: ['c', 'b', 'a']\nestimate: 5\nbest_assertion: {best_assertion}\nbest_ancestor:\n\nNone"
    assert str(node) == expected, f"Got:\n{node}\nexpected:\n{expected}"

    node.best_ancestor = raire_utils.RaireNode(["c", "b"])
    expected = f"tail: ['c', 'b', 'a']\nestimate: 5\nbest_assertion: {best_assertion}\nbest_ancestor:\n\ntail: ['c', 'b']\nestimate: inf\nbest_assertion: None\nbest_ancestor:\n\nNone"

    assert str(node) == expected, f"Got:\n{node}\nexpected:\n{expected}"


def test_raire_frontier():
    node = raire_utils.RaireNode(["c", "b", "a"])
    node.best_ancestor = "b"
    node.expandable = False

    frontier = raire_utils.RaireFrontier()
    frontier.insert_node(node)
    assert frontier.nodes == [node]

    node.expandable = True
    frontier = raire_utils.RaireFrontier()
    frontier.insert_node(node)
    assert frontier.nodes == [node]

    node.estimate = 5
    frontier = raire_utils.RaireFrontier()
    frontier.insert_node(node)
    assert frontier.nodes == [node]

    node2 = raire_utils.RaireNode(["b", "a"])
    node2.best_ancestor = "b"
    node2.expandable = True
    node2.estimate = 10
    frontier.insert_node(node2)
    assert frontier.nodes == [node2, node]

    node3 = raire_utils.RaireNode(["a"])
    node3.best_ancestor = "a"
    node3.expandable = True
    node3.estimate = 1
    frontier.insert_node(node3)
    assert frontier.nodes == [node2, node, node3]

    frontier.replace_descendents(node3)
    assert frontier.nodes == [node3, node3]

    other = raire_utils.RaireFrontier()
    other.insert_node(node3)
    other.insert_node(node3)
    assert other == frontier

    assert str(other) == str([node3, node3])


def test_find_best_audit_simple():
    contest = Contest(
        "Contest A",
        {
            "winner": 60000,
            "loser": 40000,
            "ballots": 100000,
            "numWinners": 1,
            "votesAllowed": 1,
        },
    )

    ballots = []
    for _ in range(60000):
        ballots.append({"Contest A": {"winner": 1, "loser": 2}})
    for _ in range(40000):
        ballots.append({"Contest A": {"winner": 2, "loser": 1}})

    neb_matrix = {
        "winner": {"loser": raire_utils.NEBAssertion("Contest A", "winner", "loser")},
        "loser": {"winner": raire_utils.NEBAssertion("Contest A", "winner", "loser")},
    }

    tree = raire_utils.RaireNode(["loser", "winner"])

    # pylint: disable=invalid-name
    def asn_func(m):
        return 1 / m if m > 0 else np.inf

    raire_utils.find_best_audit(contest, ballots, neb_matrix, tree, asn_func)

    expected = raire_utils.NEBAssertion("Contest A", "winner", "loser")

    assert tree.best_assertion == expected
    assert not tree.best_assertion.subsumes(expected)
    assert not expected.subsumes(tree.best_assertion)

    assert tree.estimate == expected.difficulty


def make_neb_assertion(
    contest: Contest,
    cvrs: CVRS,
    asn_func: AsnFunc,
    winner: str,
    loser: str,
    eliminated: Set[str],
) -> NEBAssertion:
    assertion = raire_utils.NEBAssertion(contest.name, winner, loser)
    assertion.eliminated = eliminated
    votes_for_winner = sum(
        assertion.is_vote_for_winner(cvr)
        for _, cvr in cvrs.items()
        if cvr  # if is for the type checker
    )
    votes_for_loser = sum(
        assertion.is_vote_for_loser(cvr) for _, cvr in cvrs.items() if cvr
    )

    margin = votes_for_winner - votes_for_loser
    assertion.difficulty = asn_func(margin)

    return assertion


def make_nen_assertion(
    contest: Contest,
    cvrs: CVRS,
    asn_func: AsnFunc,
    winner: str,
    loser: str,
    eliminated: Set[str],
) -> NENAssertion:
    assertion = raire_utils.NENAssertion(contest.name, winner, loser, eliminated)
    votes_for_winner = sum(
        assertion.is_vote_for_winner(cvr)
        for _, cvr in cvrs.items()
        if cvr  # if is for the type checker
    )
    votes_for_loser = sum(
        assertion.is_vote_for_loser(cvr) for _, cvr in cvrs.items() if cvr
    )

    margin = votes_for_winner - votes_for_loser
    assertion.difficulty = asn_func(margin)

    assertion.rules_out = [winner, loser]

    return assertion


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


# pylint: disable=invalid-name
def asn_func(m):
    return 1 / m if m > 0 else np.inf


def test_find_best_audit_complex(contest, cvrs, ballots):
    winner_neb_loser = make_neb_assertion(
        contest, cvrs, asn_func, "winner", "loser", set()
    )
    winner_neb_loser2 = make_neb_assertion(
        contest, cvrs, asn_func, "winner", "loser2", set()
    )

    loser_neb_loser2 = make_neb_assertion(
        contest, cvrs, asn_func, "loser", "loser2", set()
    )
    loser_neb_winner = make_neb_assertion(
        contest, cvrs, asn_func, "loser", "winner", set()
    )

    loser2_neb_loser = make_neb_assertion(
        contest, cvrs, asn_func, "loser2", "loser", set()
    )
    loser2_neb_winner = make_neb_assertion(
        contest, cvrs, asn_func, "loser2", "winner", set()
    )

    neb_matrix = {
        "winner": {
            "loser": winner_neb_loser,
            "loser2": winner_neb_loser2,
        },
        "loser": {
            "loser2": loser_neb_loser2,
            "winner": loser_neb_winner,
        },
        "loser2": {
            "loser": loser2_neb_loser,
            "winner": loser2_neb_winner,
        },
    }

    # No one has been eliminated yet
    tree = raire_utils.RaireNode(["loser2", "loser", "winner"])

    raire_utils.find_best_audit(contest, ballots, neb_matrix, tree, asn_func)

    # this is the lowest cost assertion to refute
    expected = loser2_neb_loser

    # check that we get expected best assertion
    assert tree.best_assertion == expected


def test_find_best_with_eliminated(contest, cvrs, ballots):
    winner_neb_loser = make_neb_assertion(
        contest, cvrs, asn_func, "winner", "loser", set(["loser2"])
    )
    loser_neb_winner = make_neb_assertion(
        contest, cvrs, asn_func, "loser", "winner", set(["loser2"])
    )
    loser2_neb_winner = make_neb_assertion(
        contest, cvrs, asn_func, "loser2", "winner", set(["loser2"])
    )

    neb_matrix = {
        "winner": {
            "loser": winner_neb_loser,
        },
        "loser": {
            "winner": loser_neb_winner,
        },
        "loser2": {
            "winner": loser2_neb_winner,
        },
    }

    tree = raire_utils.RaireNode(["winner", "loser"])

    raire_utils.find_best_audit(contest, ballots, neb_matrix, tree, asn_func)

    # this is the lowest cost assertion to refute
    # it says that winner cannot be eliminated next, meaning that the hypothesis that
    # loser actually won cannot be shown
    expected = make_nen_assertion(
        contest, cvrs, asn_func, "winner", "loser", set(["loser2"])
    )

    # check that we get expected best assertion
    assert tree.best_assertion == expected


def test_find_best_with_wrong_elimination(contest, cvrs, ballots):

    # Now check that an accidentally eliminated candidate doesn't work
    winner_neb_loser = make_neb_assertion(
        contest, cvrs, asn_func, "winner", "loser", set(["winner"])
    )
    loser_neb_loser2 = make_neb_assertion(
        contest, cvrs, asn_func, "loser", "loser2", set(["winner"])
    )
    loser2_neb_loser = make_neb_assertion(
        contest, cvrs, asn_func, "loser2", "loser", set(["winner"])
    )

    neb_matrix = {
        "winner": {
            "loser2": winner_neb_loser,
        },
        "loser": {
            "loser2": loser_neb_loser2,
        },
        "loser2": {
            "loser": loser2_neb_loser,
        },
    }

    tree = raire_utils.RaireNode(["loser2", "loser"])

    raire_utils.find_best_audit(contest, ballots, neb_matrix, tree, asn_func)

    expected = winner_neb_loser
    expected.eliminated = ["winner"]

    # check that we get expected best assertion
    assert tree.best_assertion == expected


def test_perform_dive_impossible(contest, cvrs, ballots):
    winner_neb_loser = make_neb_assertion(
        contest, cvrs, asn_func, "winner", "loser", set(["loser2"])
    )
    winner_neb_loser2 = make_neb_assertion(
        contest, cvrs, asn_func, "winner", "loser2", set(["loser2"])
    )

    loser_neb_loser2 = make_neb_assertion(
        contest, cvrs, asn_func, "loser", "loser2", set(["loser2"])
    )
    loser_neb_winner = make_neb_assertion(
        contest, cvrs, asn_func, "loser", "winner", set(["loser2"])
    )

    loser2_neb_loser = make_neb_assertion(
        contest, cvrs, asn_func, "loser2", "loser", set(["loser2"])
    )
    loser2_neb_winner = make_neb_assertion(
        contest, cvrs, asn_func, "loser2", "winner", set(["loser2"])
    )

    neb_matrix = {
        "winner": {
            "loser": winner_neb_loser,
            "loser2": winner_neb_loser2,
        },
        "loser": {
            "loser2": loser_neb_loser2,
            "winner": loser_neb_winner,
        },
        "loser2": {
            "loser": loser2_neb_loser,
            "winner": loser2_neb_winner,
        },
    }

    tree = raire_utils.RaireNode(["winner"])

    result = raire_utils.perform_dive(tree, contest, ballots, neb_matrix, asn_func)
    expected = np.inf

    # check that we get expected best assertion
    assert result == expected


def test_perform_dive_possible(contest, cvrs, ballots):
    winner_neb_loser = make_neb_assertion(
        contest, cvrs, asn_func, "winner", "loser", set(["loser2"])
    )
    winner_neb_loser2 = make_neb_assertion(
        contest, cvrs, asn_func, "winner", "loser2", set(["loser2"])
    )

    loser_neb_loser2 = make_neb_assertion(
        contest, cvrs, asn_func, "loser", "loser2", set(["loser2"])
    )
    loser_neb_winner = make_neb_assertion(
        contest, cvrs, asn_func, "loser", "winner", set(["loser2"])
    )

    loser2_neb_loser = make_neb_assertion(
        contest, cvrs, asn_func, "loser2", "loser", set(["loser2"])
    )
    loser2_neb_winner = make_neb_assertion(
        contest, cvrs, asn_func, "loser2", "winner", set(["loser2"])
    )

    neb_matrix = {
        "winner": {
            "loser": winner_neb_loser,
            "loser2": winner_neb_loser2,
        },
        "loser": {
            "loser2": loser_neb_loser2,
            "winner": loser_neb_winner,
        },
        "loser2": {
            "loser": loser2_neb_loser,
            "winner": loser2_neb_winner,
        },
    }

    tree = raire_utils.RaireNode(["loser"])

    result = raire_utils.perform_dive(tree, contest, ballots, neb_matrix, asn_func)
    expected = make_nen_assertion(
        contest, cvrs, asn_func, "winner", "loser", set(["loser2"])
    )

    assert result == expected.difficulty
