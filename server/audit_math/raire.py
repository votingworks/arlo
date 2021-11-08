from typing import Callable, Dict, Optional, List

import numpy as np

from .sampler_contest import Contest, CVR
from .raire_utils import (
    NEBAssertion,
    RaireAssertion,
    RaireFrontier,
    RaireNode,
    find_best_audit,
    perform_dive,
)


def compute_raire_assertions(
    contest: Contest, cvrs: List[CVR], winner: str, asn_func: Callable, agap=0,
) -> list:

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

        winner         - reported winner of the contest

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

    ncands = len(contest.candidates)

    # First look at all of the NEB assertions that could be formed for
    # this contest. We will refer to this matrix when examining the best
    # way to prune branches of the "alternate outcome space".
    nebs: Dict[str, Dict[str, Optional[NEBAssertion]]] = {
        c: {d: None for d in contest.candidates} for c in contest.candidates
    }

    for cand in contest.candidates:
        for other in contest.candidates:
            if cand == other:
                continue

            asrn: NEBAssertion = NEBAssertion(contest.name, cand, other)

            tally_cand: int = 0
            tally_other: int = 0
            for cvr in cvrs:
                if cvr:
                    tally_cand += asrn.is_vote_for_winner(cvr)
                    tally_other += asrn.is_vote_for_loser(cvr)

            if tally_cand > tally_other:
                asrn.margin = tally_cand - tally_other
                asrn.difficulty = asn_func(asrn.margin)

                asrn.votes_for_winner = tally_cand
                asrn.votes_for_loser = tally_other

                nebs[cand][other] = asrn

    # The RAIRE algorithm progressively searches through the space of
    # alternate election outcomes, viewing this space as a tree. We store
    # the current leaves of this tree, at any point in the search, in a
    # list called 'frontier'. Each leaf is a (potentially) partial election
    # outcome, describing the tail of the elimination sequence and eventual
    # winner. All candidates not mentioned in this tail are assumed to have
    # already been eliminated.

    # This is a running lowerbound on the overall difficulty of the
    # election audit.
    lowerbound = -10.0

    # Construct initial frontier.
    frontier = RaireFrontier()

    # Our frontier initially has a node for each alternate election outcome
    # tail of size two. The last candidate in the tail is the ultimate winner.
    for cand in contest.candidates:
        if cand == winner:
            continue

        for other in contest.candidates:
            if cand == other:
                continue

            newn = RaireNode([other, cand])
            newn.expandable = ncands > 2

            find_best_audit(contest, cvrs, nebs, newn, asn_func)
            frontier.insert_node(newn)

    # Flag to keep track of whether a full manual recount will be required
    audit_not_possible = False

    # -------------------- Find Assertions -----------------------------------
    while not audit_not_possible:
        # Check whether we can stop searching for assertions.
        max_on_frontier = max([node.estimate for node in frontier.nodes])

        if agap > 0 and lowerbound > 0 and max_on_frontier - lowerbound <= agap:
            # We can rule out all branches of the tree with assertions that
            # have a difficulty that is <= lowerbound.
            break

        to_expand = frontier.nodes[0]

        # We can also stop searching if all nodes on our frontier are leaves.
        if not to_expand.expandable:
            break

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
        dive_lb = perform_dive(to_expand, contest, cvrs, nebs, asn_func)

        if dive_lb == np.inf:
            # The particular branch we dived along cannot be ruled out
            # with an assertion.
            audit_not_possible = True
            break

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
                newn.expandable = not len(newn.tail) == ncands

                # Assign a 'best ancestor' to the new node.
                newn.best_ancestor = (
                    to_expand.best_ancestor
                    if to_expand.best_ancestor
                    and to_expand.best_ancestor.estimate <= to_expand.estimate
                    else to_expand
                )

                find_best_audit(contest, cvrs, nebs, newn, asn_func)

                if not newn.expandable:
                    # 'newn' is a leaf.
                    if (
                        newn.estimate == np.inf
                        and newn.best_ancestor
                        and newn.best_ancestor.estimate == np.inf
                    ):

                        audit_not_possible = True

                        break

                    if (
                        newn.best_ancestor
                        and newn.best_ancestor.estimate <= newn.estimate
                    ):
                        lowerbound = max(lowerbound, newn.best_ancestor.estimate)
                        frontier.replace_descendents(newn.best_ancestor)

                    else:
                        lowerbound = max(lowerbound, newn.estimate)
                        frontier.insert_node(newn)

                else:
                    frontier.insert_node(newn)

            if audit_not_possible:
                break

        if audit_not_possible:
            break

    # If a full recount is required, return empty list.
    if audit_not_possible:
        return []

    # ------------------------------------------------------------------------
    assertions: List[RaireAssertion] = []

    # Some assertions will be used to rule out multiple branches of our
    # alternate outcome tree. Form a list of all these assertions, without
    # duplicates.
    for node in frontier.nodes:
        skip = False
        for assrtn in assertions:
            if node.best_assertion == assrtn:
                skip = True
                break

        if not skip:
            assertions.append(node.best_assertion)

    # Assertions will be sorted in order of greatest to least difficulty.
    sorted_assertions = sorted(assertions)
    len_assertions = len(sorted_assertions)

    final_audit = []

    # Some assertions will "subsume" others. For example, an assertion
    # that says "Candidate A cannot be eliminated before candidate B" will
    # subsume all NEN assertions that say A is not eliminated next when B
    # is still standing. What this means is that if the NEB assertion holds,
    # the NEN assertion will hold, so there is no need to check both of them.
    for i in range(len_assertions):
        assrtn_i = sorted_assertions[i]

        subsumed = False
        for j in range(len_assertions):

            if i == j:
                continue

            assrtn_j = sorted_assertions[j]

            if assrtn_j.subsumes(assrtn_i):
                subsumed = True

                break

        if not subsumed:
            final_audit.append(assrtn_i)

    return final_audit
