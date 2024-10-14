from typing import Callable, Dict, Optional, List

import numpy as np

from .sampler_contest import Contest
from .raire_utils import (
    NEBAssertion,
    RaireAssertion,
    RaireFrontier,
    RaireNode,
    find_best_audit,
    perform_dive,
    CVRS,
)


NEBMatrix = Dict[str, Dict[str, Optional[NEBAssertion]]]


def make_neb_matrix(contest: Contest, cvrs: CVRS, asn_func) -> NEBMatrix:
    """
    Builds the NEB matrix for use by find_best_audit.

    Input:
        contest     - the contest being audited
        cvrs        - a list of CVRS to be audited
        asn_func    - the asn function to find assertion difficulty
    Output:
        neb_matrix  - a dict of dicts mapping candidate pairs to assertions
    """
    nebs: NEBMatrix = {
        c: {d: None for d in contest.candidates} for c in contest.candidates
    }

    for cand in contest.candidates:
        for other in contest.candidates:
            if cand == other:
                continue

            asrn: NEBAssertion = NEBAssertion(contest.name, cand, other)

            tally_cand: int = 0
            tally_other: int = 0
            for _, cvr in cvrs.items():
                assert cvr is not None  # for type checker
                tally_cand += asrn.is_vote_for_winner(cvr)
                tally_other += asrn.is_vote_for_loser(cvr)

            if tally_cand > tally_other and other not in contest.winners:
                margin = tally_cand - tally_other
                asrn.difficulty = asn_func(margin)

                nebs[cand][other] = asrn

    return nebs


def make_frontier(
    contest: Contest,
    ballots: List[Dict[str, int]],
    nebs: NEBMatrix,
    asn_func,
) -> RaireFrontier:
    """
    Constructs the frontier for the search for the best audit

    """
    frontier = RaireFrontier()

    # Our frontier initially has a node for each alternate election outcome
    # tail of size two. The last candidate in the tail is the ultimate winner.
    for cand in contest.candidates:
        if cand in contest.winners:
            # We don't care about other winners
            continue

        for other in contest.candidates:
            if cand == other:
                continue

            newn = RaireNode([other, cand])
            newn.expandable = len(contest.candidates) > 2

            find_best_audit(contest, ballots, nebs, newn, asn_func)
            frontier.insert_node(newn)

    return frontier


def find_assertions(
    contest: Contest,
    ballots: List[Dict[str, int]],
    nebs: NEBMatrix,
    asn_func: Callable,
    frontier: RaireFrontier,
    lowerbound: float,
    agap: float,
) -> bool:
    """
    Find the best assertions for frontier, and mutate frontier accordingly.

    """
    audit_possible = True
    while audit_possible:
        # Check whether we can stop searching for assertions.
        max_on_frontier = max(node.estimate for node in frontier.nodes)

        if agap > 0 and lowerbound > 0 and max_on_frontier - lowerbound <= agap:
            # We can rule out all branches of the tree with assertions that
            # have a difficulty that is <= lowerbound.
            return True

        to_expand = frontier.nodes[0]

        # We can also stop searching if all nodes on our frontier are leaves.
        if not to_expand.expandable:
            return True

        frontier.nodes.pop(0)

        if to_expand.best_ancestor and to_expand.best_ancestor.estimate <= lowerbound:
            frontier.replace_descendents(to_expand.best_ancestor)
            continue

        if to_expand.estimate <= lowerbound:
            to_expand.expandable = False
            frontier.insert_node(to_expand)
            continue

        # --------------------------------------------------------------------
        # "Dive" straight from "to_expand" down to a leaf -- one of its
        # decendents -- and find the least cost assertion to rule out the
        # branch of the alternate outcomes tree that ends in that leaf. We
        # know that this assertion will be part of the audit, as we have
        # to rule out all branches.
        dive_lb = perform_dive(to_expand, contest, ballots, nebs, asn_func)

        if dive_lb == np.inf:
            # The particular branch we dived along cannot be ruled out
            # with an assertion.
            return False

        # We can use our new knowledge of the "best" way to rule out
        # the branch to update our "lowerbound" on the overall "difficulty"
        # of the eventual audit.
        lowerbound = max(lowerbound, dive_lb)

        if to_expand.best_ancestor and to_expand.best_ancestor.estimate <= lowerbound:
            frontier.replace_descendents(to_expand.best_ancestor)
            continue

        if to_expand.estimate <= lowerbound:
            to_expand.expandable = False
            frontier.insert_node(to_expand)
            continue
        # --------------------------------------------------------------------

        # Find children of current node, and find the best assertions that
        # could be used to prune those nodes from the tree of alternate
        # outcomes.
        for cand in contest.candidates:
            if not cand in to_expand.tail:
                newn = RaireNode([cand] + to_expand.tail)
                newn.expandable = len(newn.tail) < len(contest.candidates)

                # Assign a 'best ancestor' to the new node.
                newn.best_ancestor = (
                    to_expand.best_ancestor
                    if to_expand.best_ancestor
                    and to_expand.best_ancestor.estimate <= to_expand.estimate
                    else to_expand
                )
                # This is for the type checker...
                assert newn.best_ancestor

                find_best_audit(contest, ballots, nebs, newn, asn_func)

                if not newn.expandable:
                    # 'newn' is a leaf.
                    if (
                        newn.estimate == np.inf
                        and newn.best_ancestor.estimate == np.inf
                    ):
                        return False

                    lowerbound = max(lowerbound, newn.best_ancestor.estimate)
                    frontier.replace_descendents(newn.best_ancestor)
                else:
                    frontier.insert_node(newn)
    return False  # pragma: no cover


def compute_raire_assertions(
    contest: Contest,
    cvrs: CVRS,
    asn_func: Callable,
    agap: float = 0.0,
) -> List[RaireAssertion]:
    """

    Inputs:
        contest        - the contest and results being audited

        cvrs           - mapping of ballot_id to votes:
                {
                    'ballot_id': {
                        'contest': {
                            'candidate1': 1,
                            'candidate2': 0,
                            'candidate3': 2,
                            'candidate4': 3,
                            ...
                        }
                    ...
                }


        asn_func       - function that takes a margin as input and
                         returns an estimate of how difficult a
                         RAIRE assertion with that margin will be
                         to audit.

        agap           - allowed gap between the lower and upper bound
                         on expected audit difficulty. Once these bounds
                         converge (to within 'agap') algorithm can stop
                         and return  audit configuration found. Generally,
                         keep this at 0 unless the algorithm is not
                         terminating in a reasonable time. Then set it to
                         as small a value as possible, and increase, until
                         the algorithm terminates. For some instances, the
                         difference between the lower and upper bound on
                         expected audit difficulty gets to a point where it
                         is quite small, but doesn't converge.

    Outputs:
        A list of RaireAssertions to be audited. If this collection of
        assertions is found to hold, then all alternate outcomes, in which
        an alternate candidate to 'winner' wins, can be ruled out.
    """
    # First look at all of the NEB assertions that could be formed for
    # this contest. We will refer to this matrix when examining the best
    # way to prune branches of the "alternate outcome space".
    nebs: Dict[str, Dict[str, Optional[NEBAssertion]]] = make_neb_matrix(
        contest, cvrs, asn_func
    )

    # The RAIRE algorithm progressively searches through the space of
    # alternate election outcomes, viewing this space as a tree. We store
    # the current leaves of this tree, at any point in the search, in a
    # list called 'frontier'. Each leaf is a (potentially) partial election
    # outcome, describing the tail of the elimination sequence and eventual
    # winner. All candidates not mentioned in this tail are assumed to have
    # already been eliminated.

    # Construct initial frontier.
    ballots = [
        blt[contest.name] for _, blt in cvrs.items() if blt and contest.name in blt
    ]
    frontier = make_frontier(contest, ballots, nebs, asn_func)

    # This is a running lowerbound on the overall difficulty of the
    # election audit.
    lowerbound = -10.0

    # -------------------- Find Assertions -----------------------------------
    if not find_assertions(
        contest, ballots, nebs, asn_func, frontier, lowerbound, agap
    ):
        # If the audit isn't possible, we need a full recount
        return []
    # ------------------------------------------------------------------------
    # Some assertions will be used to rule out multiple branches of our
    # alternate outcome tree. Form a list of all these assertions, without
    # duplicates.
    assertions: List[RaireAssertion] = list(
        set(
            node.best_assertion
            for node in frontier.nodes
            if node.best_assertion is not None
        )
    )

    # Assertions will be sorted in order of greatest to least difficulty.
    # Some assertions will "subsume" others. For example, an assertion
    # that says "Candidate A cannot be eliminated before candidate B" will
    # subsume all NEN assertions that say A is not eliminated next when B
    # is still standing. What this means is that if the NEB assertion holds,
    # the NEN assertion will hold, so there is no need to check both of them.
    final_audit = list(
        sorted(
            assertion
            for assertion in assertions
            if not any(
                other_assertion.subsumes(assertion)
                for other_assertion in assertions
                if other_assertion != assertion
            )
        )
    )

    return final_audit
