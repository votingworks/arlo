from .sampler_contest import Contest, CVRS, SAMPLECVRS, CVR
from .raire_utils import NENAssertion, NEBAssertion, RaireAssertion, \
    RaireFrontier, RaireNode, find_best_audit, perform_dive

from typing import Callable
import numpy as np

import sys


def compute_raire_assertions(
    contest: Contest, cvrs: CVRS, winner: str, asn_func: Callable,
    log: bool, stream=sys.stdout
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

        log            - flag indicating if logging statements should
                         be printed during the algorithm.

        stream         - stream to which logging statements should
                         be printed.

    Outputs:
        A list of RaireAssertions to be audited. If this collection of
        assertions is found to hold, then all alternate outcomes, in which
        an alternate candidate to 'winner' wins, can be ruled out. 
    """

    ncands = len(contest.candidates)

    # First look at all of the NEB assertions that could be formed for
    # this contest. We will refer to this matrix when examining the best
    # way to prune branches of the "alternate outcome space". 
    nebs = {c : { d : None for d in contest.candidates} 
        for c in contest.candidates} 

    for c in contest.candidates:
        for d in contest.candidates:
            if c == d: 
                continue

            asrn = NEBAssertion(contest.name, c, d)
            tally_c = np.sum(
                [asrn.is_vote_for_winner(r) for _,r in cvrs.items()]
            )

            tally_d = np.sum(
                [asrn.is_vote_for_loser(r) for _,r in cvrs.items()]
            )

            if tally_c > tally_d:
                asrn.margin = tally_c - tally_d
                asrn.difficulty = asn_func(asrn.margin)

                nebs[c][d] = asrn

                asrn.display()


    # The RAIRE algorithm progressively searches through the space of 
    # alternate election outcomes, viewing this space as a tree. We store
    # the current leaves of this tree, at any point in the search, in a 
    # list called 'frontier'. Each leaf is a (potentially) partial election
    # outcome, describing the tail of the elimination sequence and eventual
    # winner. All candidates not mentioned in this tail are assumed to have
    # already been eliminated. 

    ballots = [blt[contest.name] for _,blt in cvrs.items() 
        if contest.name in blt]

    # This is a running lowerbound on the overall difficulty of the 
    # election audit. 
    lowerbound = -10

    # Construct initial frontier. 
    frontier = RaireFrontier()

    # Our frontier initially has a node for each alternate election outcome
    # tail of size two. The last candidate in the tail is the ultimate winner. 
    for c in contest.candidates:
        if c == winner: continue

        for d in contest.candidates:
            if c == d: continue

            newn = RaireNode([d,c])
            newn.expandable = True if ncands > 2 else False

            find_best_audit(contest, ballots, nebs, newn, asn_func)

            if log:
                print("TESTED ", file=stream, end='')
                newn.display(stream=stream)

            frontier.insert_node(newn)

    # Flag to keep track of whether a full manual recount will be required
    audit_not_possible = False

    if log:
        print("===============================================", file=stream)
        print("Initial Frontier", file=stream)
        frontier.display(stream=stream)
        print("===============================================", file=stream)
    
    # -------------------- Find Assertions -----------------------------------
    while not audit_not_possible:
        # Check whether we can stop searching for assertions.
        max_on_frontier = max([node.estimate for node in frontier.nodes])

        if max_on_frontier == lowerbound:
            # We can rule out all branches of the tree with assertions that
            # have a difficulty that is <= lowerbound. 
            break

        if log:
            print("Max on frontier {}, lowerbound {}".format(max_on_frontier,
                lowerbound), file=stream)

        to_expand = frontier.nodes.pop(0)

        # We can also stop searching if all nodes on our frontier are leaves.
        if not to_expand.expandable:
            break

        if to_expand.best_ancestor != None and \
            to_expand.best_ancestor.estimate <= lowerbound:
            frontier.replace_descendents(to_expand.best_anscestor, log,
                stream=stream)
            continue

        if to_expand.estimate <= lowerbound:
            to_expand.expandable = False
            fontier.insert_node(to_expand)
            continue

        #--------------------------------------------------------------------
        # "Dive" straight from "to_expand" down to a leaf -- one of its
        # decendents -- and find the least cost assertion to rule out the
        # branch of the alternate outcomes tree that ends in that leaf. We
        # know that this assertion will be part of the audit, as we have
        # to rule out all branches. 
        dive_lb = perform_dive(to_expand, contest, ballots, nebs, asn_func)

        if dive_lb == np.inf:
            # The particular branch we dived along cannot be ruled out
            # with an assertion.
            audit_not_possible = True
            if log:
                print("Diving finds that audit is not possible",
                    file=stream)
            break

        if log:
            print("Diving LB {}, Current LB {}".format(dive_lb, 
                lowerbound), file=stream)

        # We can use our new knowledge of the "best" way to rule out
        # the branch to update our "lowerbound" on the overall "difficulty"
        # of the eventual audit.
        lowerbound = max(lowerbound, dive_lb)

        if to_expand.best_ancestor != None and \
            to_expand.best_ancestor.estimate <= lowerbound:
            frontier.replace_descendents(to_expand.best_anscestor)
            continue

        if to_expand.estimate <= lowerbound:
            to_expand.expandable = False
            fontier.insert_node(to_expand)
            continue
        #--------------------------------------------------------------------

        if log:
            print("  Expanding node ", file=stream, end='')
            to_expand.display(stream=stream)

        # Find children of current node, and find the best assertions that 
        # could be used to prune those nodes from the tree of alternate
        # outcomes.
        for c in contest.candidates:
            if not c in to_expand.tail:
                newn = RaireNode([c] + to_expand.tail)
                newn.expandable = False if len(newn.tail) == ncands else True

                # Assign a 'best ancestor' to the new node. 
                newn.best_ancestor = to_expand.best_ancestor if \
                    to_expand.best_ancestor != None and \
                    to_expand.best_ancestor.estimate <= to_expand.estimate \
                    else to_expand

                find_best_audit(contest, ballots, nebs, newn, asn_func)

                if log:
                    print("TESTED ", file=stream, end='')
                    newn.display(stream=stream)

                if not newn.expandable:
                    # 'newn' is a leaf.
                    if newn.estimate == np.inf and \
                        newn.best_ancestor.estimate == np.inf:

                        audit_not_possible = True

                        if log:
                            print("Found branch that cannot be pruned.",
                                file=stream)
                        break

                    if newn.best_ancestor.estimate <= newn.estimate:
                        lowerbound=max(lowerbound,newn.best_ancestor.estimate)
                        frontier.replace_descendents(newn.best_ancestor, log,
                            stream=stream)
                    else:
                        lowerbound=max(lowerbound,newn.estimate)
                        frontier.insert_node(newn)

                        if log:
                            print("    Best audit ", file=stream, end='')
                            newn.best_assertion.display(stream=stream)
                else:
                    frontier.insert_node(newn)
                    if log:
                        if newn.best_assertion != None:
                            print("    Best audit ", file=stream, end='')
                            newn.best_assertion.display(stream=stream)
                        else:
                            print("    Cannot be disproved", file=stream)

            if audit_not_possible: break    

        
        if log:
            print("Size of frontier {}, current lower bound {}".format(
                len(frontier.nodes), lowerbound))

        if audit_not_possible: break 

    # If a full recount is required, return empty list.
    if audit_not_possible: 
        if log:
            print("AUDIT NOT POSSIBLE", file=stream)

        return []

    # ------------------------------------------------------------------------

    assertions = [node.best_assertion for node in frontier.nodes]

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
        for j in range(i, len_assertions):
            assrtn_j = sorted_assertions[i]
            
            if assertn_j.subsumes(assrtn_i):
                subsumed = True
                break

        if not subsumed:
            final_audit.appned(assrtn_i)

    if log:
        print("===============================================", file=stream)
        print("ASSERTIONS:", file=stream)
        for assertion in final_audit:
            assertion.display(stream=stream)
        print("===============================================", file=stream)
        
    return final_audit  
