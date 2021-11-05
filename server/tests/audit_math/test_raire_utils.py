from typing import List, Any

from server.audit_math.sampler_contest import Contest

import server.audit_math.raire_utils as raire_utils


def test_ranking_not_on_ballots():
    cand = "not on ballot"
    ballot: raire_utils.CB = {
        "A": 1,
        "B": 2,
        "C": 3,
    }

    assert raire_utils.ranking(cand, ballot) == -1


def test_ranking():
    ballot: raire_utils.CB = {
        "A": 1,
        "B": 2,
        "C": 3,
        "D": 0,
        "E": "not present",
    }

    assert raire_utils.ranking("A", ballot) == 1
    assert raire_utils.ranking("D", ballot) == -1
    assert raire_utils.ranking("E", ballot) == -1


def test_vote_for_candidate():
    ballot: raire_utils.CB = {
        "A": 1,
        "B": 2,
        "C": 3,
        "D": 0,
        "E": "not present",
    }

    assert raire_utils.vote_for_cand("A", [], ballot)
    assert not raire_utils.vote_for_cand("B", [], ballot)
    assert raire_utils.vote_for_cand("B", ["A"], ballot)
    assert not raire_utils.vote_for_cand("D", [], ballot)


def test_vote_for_eliminated_cand():
    cand = "C"
    ballot: raire_utils.CB = {
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
    ), f"__ls__ failed! {asrtn_1.difficulty} {asrtn_2.difficulty}"


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

    cvr = {"Contest A": {"winner": 1, "loser": 2}}
    assert asrtn_1.is_vote_for_winner(cvr) == 1
    assert asrtn_1.is_vote_for_loser(cvr) == 0

    assert asrtn_1.same_as(asrtn_1)


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
    asrtn_3.rules_out: List[Any] = ["winner", "loser"]
    assert asrtn_1.subsumes(asrtn_3)

    asrtn_3.rules_out: List[Any] = []
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

    assert asrtn_1.same_as(asrtn_1)


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


def test_raire_node_descendents():

    parent = raire_utils.RaireNode(["b", "a"])
    not_child = raire_utils.RaireNode(["c", "a"])

    # These are two unrelated nodes
    assert not not_child.is_descendent_of(parent)
    assert not parent.is_descendent_of(not_child)

    child = raire_utils.RaireNode(["c", "b", "a"])
    assert child.is_descendent_of(parent)
    assert not child.is_descendent_of(not_child)


def test_raire_node_repr():
    node = raire_utils.RaireNode(["c", "b", "a"])
    node.estimate = 5
    node.best_ancestor = "b"

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

    expected = f"tail: ['c', 'b', 'a']\n\
                \testimate: 5\n\
                \tbest_ancestor: b\n\
                \tbest_assertion: {best_assertion}"

    assert str(node) == expected


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
