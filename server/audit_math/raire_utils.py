from __future__ import annotations
from typing import Type, Callable, Dict, List, Any, Optional, Literal, Set, TypedDict
import numpy as np

from .sampler_contest import Contest

# Note: these types are slightly different from the Arlo CVR types defined in
# sampler_contest.py, since they use ints to represent votes instead of strings.
# Our RAIRE implementation currently doesn't support the special casing for ES&S
# overvotes/undervotes that the other audit math does which requires string CVR
# values. For now, it's simplest to just redefine the types here.

# CVR: { contest_id: { choice_id: 0 | 1 }}
# CVRS: { ballot_id: CVR }
CVR = Dict[str, Dict[str, int]]
CVRS = Dict[str, Optional[CVR]]


class SampleCVR(TypedDict):
    times_sampled: int
    cvr: Optional[CVR]


SAMPLECVRS = Dict[str, SampleCVR]


def ranking(cand: str, ballot: Dict[str, int]) -> int:
    """
    Input:
        cand : string  -   identifier for candidate
        ballot :       -   mapping between candidate name and their
                           position in the ranking for a relevant contest
                           on a given ballot.

    Output:
        Returns the position of candidate 'cand' in the ranking of the
        given ballot 'ballot'. Returns -1 if 'cand' is not preferenced on the
        ballot.
    """
    return ballot.get(cand, 0)


def vote_for_cand(
    cand: str, eliminated: Set[str], ballot: Dict[str, int]
) -> Literal[0, 1]:
    """
    Input:
        cand : string       -   identifier for candidate
        eliminated : list   -   identifiers of eliminated candidates
        ballot : CB         -   mapping between candidate name and their
                                position in the ranking for a relevant contest
                                on a given ballot.
    Output:
        Returns 1 if the given 'ballot' is a vote for the given candidate 'cand'
        in the context where candidates in 'eliminated' have been eliminated.
        Otherwise, return 0 as the 'ballot' is not a vote for 'cand'.
    """
    # If 'cand' is not in the set of candidates assumed still standing,
    # 'cand' does not get this vote.
    if cand in eliminated:
        return 0

    # If 'cand' does not appear on the ballot, they do not get this vote.
    c_idx = ranking(cand, ballot)
    if not c_idx:
        return 0

    for alt_c, a_idx in ballot.items():
        if alt_c == cand:
            continue

        if alt_c in eliminated:
            continue

        if a_idx and a_idx < c_idx:
            return 0

    return 1


class RaireAssertion:
    def __init__(self, contest: str, winner: str, loser: str):
        """
        Initializes a RAIRE assertion involving a comparison between
        the tallies of a candidate labelled 'winner' and a candidate
        labelled 'loser'. This assertion 'asserts' that the tally of
        the winner is larger than the tally of the loser in some context.

        Each assertion will have an estimated 'difficulty' related to
        the anticipated number of ballot checks required to audit it.

        Each assertion will have a margin defined as the difference in
        tallies ascribed to 'winner' and 'loser'
        """

        self.contest = contest

        self.winner = winner
        self.loser = loser

        self.difficulty = np.inf

        self.rules_out: List[Any] = []
        self.eliminated: Set = set()

    def is_vote_for_winner(self, cvr: CVR):
        """
        Input:
            cvr - cast vote record

        Output:
            Returns 1 if the given cvr represents a vote for the assertions
            winner, and 0 otherwise.
        """

    def is_vote_for_loser(self, cvr: CVR):
        """
        Input:
            cvr - cast vote record

        Output:
            Returns 1 if the given cvr represents a vote for the assertions
            loser, and 0 otherwise.
        """

    def subsumes(self, other):
        """
        Returns true if this assertion 'subsumes' the input assertion 'other'.
        An assertion 'A' subsumes assertion 'B' if the alternate outcomes
        ruled out by 'B' is a subset of those ruled out by 'A'. If we include
        'A' in an audit, we don't need to include 'B'.

        Input:
        other : RaireAssertion   - Assertion 'B'

        Output:
        Returns true if this assertion subsumes assertion 'other'.
        """

    def __eq__(self, other):
        """
        Returns True if this assertion is equal to 'other' (i.e., they
        are the same assertion), and False otherwise.
        """

    # Assertions are ordered from greatest to least difficulty.
    def __lt__(self, other):
        return self.difficulty > other.difficulty

    def __gt__(self, other):
        return self.difficulty < other.difficulty

    def __repr__(self):
        return f"{self.contest} {self.winner} {self.loser} {self.difficulty}"


class NEBAssertion(RaireAssertion):
    """
    A Not-Eliminated-Before (NEB) assertion between a candidate 'winner' and
    a candidate 'loser' compares the minimum possible tally 'winner' could
    have (their first preference tally) with the maximum possible tally
    candidate 'loser' could have while 'winner' is still standing.

    We give 'winner' only those votes that rank 'winner' first.

    We give 'loser' ALL votes in which 'loser' appears in the ranking and
    'winner' does not, or 'loser' is ranked higher than 'winner'.

    This assertion "asserts" that the tally of 'winner' is larger than the
    tally of the 'loser'. This means that 'winner' could never be eliminated
    prior to 'loser'.
    """

    def is_vote_for_winner(self, cvr: CVR) -> Literal[0, 1]:
        return (
            1
            if self.contest in cvr and ranking(self.winner, cvr[self.contest]) == 1
            else 0
        )

    def is_vote_for_loser(self, cvr: CVR) -> Literal[0, 1]:
        if self.contest not in cvr:
            return 0
        w_idx = ranking(self.winner, cvr[self.contest])
        l_idx = ranking(self.loser, cvr[self.contest])

        return 1 if l_idx and (not w_idx or l_idx < w_idx) else 0

    def subsumes(self, other: Type[RaireAssertion]) -> bool:
        """
        An NEBAssertion 'A' subsumes an assertion 'other' if:
        - 'other' is not an NEBAssertion and one of the following is true:
            - Both assertions have the same winner & loser
            - 'other' rules out an outcome with the tail 'Tail' and either the
              winner of this NEBAssertion assertion appears before the loser in
              'Tail' or the loser appears and the winner does not.
        """
        if isinstance(other, NEBAssertion):
            return False

        if self.winner == other.winner and self.loser == other.loser:
            return True

        if other.rules_out:
            # If self.winner appears before self.loser in the list
            # 'other.rules_out', or self.loser appears and self.winner does
            # not, then this assertion subsumes 'other'.
            idx_winner = (
                other.rules_out.index(self.winner)
                if self.winner in other.rules_out
                else -1
            )
            idx_loser = (
                other.rules_out.index(self.loser)
                if self.loser in other.rules_out
                else -1
            )

            if idx_winner < idx_loser:
                return True

        return False

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, NEBAssertion)
            and self.contest == other.contest
            and self.winner == other.winner
            and self.loser == other.loser
        )

    def __hash__(self) -> int:
        return hash((self.contest, self.winner, self.loser))

    def __repr__(self) -> str:
        return f"NEB,Winner,{self.winner},Loser,{self.loser},Eliminated"


class NENAssertion(RaireAssertion):
    """
    A Not-Eliminated-Next (NEN) assertion between a candidate 'winner' and
    a candidate 'loser' compares the tally of the two candidates in the
    context where a given set of candidates have been eliminated.

    We give 'winner' all votes in which they are preferenced first AFTER
    the candidates in 'eliminated' are removed from the ranking.

    We give 'loser' all votes in which they are preferenced first AFTER
    the candidates in 'eliminated' are removed from the ranking.

    This assertion "asserts" that the tally of the 'winner' in this context,
    where the specified candidates have been eliminated, is larger than that
    of 'loser'.
    """

    def __init__(self, contest: str, winner: str, loser: str, eliminated: Set[str]):
        super().__init__(contest, winner, loser)

        self.eliminated = eliminated

    def is_vote_for_winner(self, cvr: CVR) -> Literal[0, 1]:
        if not self.contest in cvr:
            return 0

        return vote_for_cand(self.winner, self.eliminated, cvr[self.contest])

    def is_vote_for_loser(self, cvr: CVR) -> Literal[0, 1]:
        if not self.contest in cvr:
            return 0

        return vote_for_cand(self.loser, self.eliminated, cvr[self.contest])

    def subsumes(self, other: RaireAssertion) -> bool:
        """
        An NENAssertion 'A' subsumes an assertion 'other' if 'other' is
        not an NEBAssertion, they have the same winner, and rule out
        Tail sequences that contain same set of candidates.
        """

        if isinstance(other, NEBAssertion):
            return False

        if self.winner == other.winner and set(self.rules_out) == set(other.rules_out):
            return True

        return False

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, NENAssertion)
            and self.contest == other.contest
            and self.winner == other.winner
            and self.loser == other.loser
            and self.eliminated == other.eliminated
        )

    def __hash__(self) -> int:
        return hash((self.contest, self.winner, self.loser, tuple(self.eliminated)))

    def __repr__(self) -> str:
        return f"NEN,Winner,{self.winner},Loser,{self.loser},Eliminated," + ",".join(
            self.eliminated
        )


class RaireNode:
    def __init__(self, tail: List[str]):
        # Tail of an "imagined" elimination sequence representing the
        # outcome of an IRV election. The last candidate in the tail is
        # the "imagined" winner of the election.
        self.tail = tail  # List of str (candidate identifiers)

        # If there are candidates not mentioned in self.tail, this node
        # is not a leaf and it can be expanded.
        self.expandable = True

        # Estimate of difficulty of ruling out the outcome this node
        # represents.
        self.estimate = np.inf

        # Lowest cost assertion that, if true, can rule out any election
        # outcome that *ends* with the given tail.
        self.best_assertion: Optional[RaireAssertion] = None

        self.best_ancestor: Optional[RaireNode] = None

    def is_descendent_of(self, node: RaireNode) -> bool:
        """
        Determines if the given 'node' is an ancestor of this node in a
        tree of possible election outcomes. A node with a tail equal to
        [a,b,c,d] has ancestors with tails [b,c,d], [c,d], and [d].

        Input:
        node: RaireNode     -  Potential ancestor

        Output:
        Returns True if the input 'node' is an ancestor of this node, and
        False otherwise.
        """
        len1 = len(self.tail)
        len2 = len(node.tail)

        if len1 <= len2:
            return False

        return self.tail[len1 - len2 :] == node.tail

    def __eq__(self, other):
        return (
            self.estimate == other.estimate
            and self.best_assertion == other.best_assertion
            and self.best_ancestor == other.best_ancestor
            and self.tail == other.tail
        )

    def __repr__(self):
        return f"tail: {self.tail}\nestimate: {self.estimate}\nbest_assertion: {self.best_assertion}\nbest_ancestor:\n\n{self.best_ancestor}"


class RaireFrontier:
    def __init__(self):
        self.nodes = []

    def insert_node(self, node: RaireNode):
        """
        Insert given node into the frontier in the right position. Nodes
        that are not associated with an "invalidating" assertion are placed
        at the front of the frontier. After these nodes, nodes in frontier
        are ordered from most difficult to invalidate to easiest to
        invalidate. Leaf nodes -- nodes whose "tail" contains all candidates
        -- are placed at the end of the frontier.

        Input:
            node: RaireNode   - node, representing an alternate election
                                outcome, to add to the frontier.
        """
        if not node.expandable:
            self.nodes.append(node)

        elif node.estimate == np.inf:
            self.nodes.insert(0, node)

        else:
            i = 0
            while i < len(self.nodes):
                n_est = self.nodes[i].estimate

                if n_est <= node.estimate:
                    break

                i += 1

            self.nodes.insert(i, node)

    def replace_descendents(self, node: RaireNode):
        """
        Remove all descendents of the input 'node' from the frontier, and
        insert 'node' to the frontier in the appropriate position.
        """

        self.nodes = [
            other_node
            for other_node in self.nodes
            if not other_node.is_descendent_of(node)
        ]
        self.insert_node(node)

    def __eq__(self, other):
        return self.nodes == other.nodes

    def __repr__(self):
        return str(self.nodes)


def find_best_audit(
    contest: Contest,
    ballots: List[Dict[str, int]],
    neb_matrix,
    node: RaireNode,
    asn_func: Callable,
):
    """
    Input:

    contest: Contest   -  Contest being audited.

    cvrs: list of CVRs -  Details of reported ballots for this contest.

    neb_matrix         -  |Candidates| x |Candidates| dictionary where
                          neb_matrix[c1][c2] returns a NEBAssertion stating
                          that c1 cannot be eliminated before c2 (if one
                          exists) and None otherwise.

    node: RaireNode    -  A node in the tree of alternate election outcomes.
                          The node represents an election outcome that ends
                          in the sequence node.tail.

    asn_func: Callable -  Function that takes an assertion margin and
                          returns an estimate of how "difficult" it will
                          be to audit that assertion.

    Output:
    Finds the least cost assertion that can be used to rule out all election
    outcomes that end with the sequence node.tail, and assigns that assertion
    to node.best_assertion. If no such assertion can be found, node.assertion
    will equal None after this function is called.
    """

    first_in_tail = node.tail[0]
    best_asrtn = None

    # We first consider if we can invalidate this outcome by showing that
    # 'first_in_tail' can not-be-eliminated-before a candidate that
    # appears later in tail.
    for later_cand in node.tail[1:]:
        # Can we show that the candidate 'later_cand' must come before
        # candidate 'first_in_tail' in the elimination sequence?
        neb = neb_matrix[first_in_tail][later_cand]

        if neb and (best_asrtn is None or neb.difficulty < best_asrtn.difficulty):
            best_asrtn = neb

    # 'eliminated' is the list of candidates that are not mentioned in 'tail'.
    eliminated = {c for c in contest.candidates if not c in node.tail}

    # We now look at whether there is a candidate not mentioned in
    # 'tail' (this means they are assumed to be eliminated at some prior
    # point in the elimination sequence), that can not-be-eliminated-before
    # 'first_in_tail'.
    for cand in eliminated:
        neb = neb_matrix[cand][first_in_tail]

        if neb and (best_asrtn is None or neb.difficulty < best_asrtn.difficulty):
            best_asrtn = neb

    # We now consider whether we can find a better NEN assertion. We
    # want to show that at the point where all the candidates in 'tail'
    # remain, 'first_in_tail' is not the candidate with the least number
    # of votes. This means that 'first_in_tail' should not be eliminated next.
    # Tally of the candidate 'first_in_tail'
    tally_first_in_tail = sum(
        vote_for_cand(first_in_tail, eliminated, blt) for blt in ballots
    )

    for later_cand in node.tail[1:]:
        tally_later_cand = sum(
            vote_for_cand(later_cand, eliminated, blt) for blt in ballots
        )

        margin = tally_first_in_tail - tally_later_cand

        if margin > 0:
            # We can create a NEN assertion that says "first_in_cand"
            # should not be eliminated next, after "eliminated" are
            # eliminated, because "later_cand" actually has less votes
            # at this point.
            estimate = asn_func(margin)

            if best_asrtn is None or estimate < best_asrtn.difficulty:
                nen = NENAssertion(contest.name, first_in_tail, later_cand, eliminated)

                nen.rules_out = node.tail
                nen.difficulty = estimate

                best_asrtn = nen

    node.best_assertion = best_asrtn

    if best_asrtn:
        node.estimate = best_asrtn.difficulty


def perform_dive(
    node: RaireNode,
    contest: Contest,
    ballots: List[Dict[str, int]],
    neb_matrix,
    asn_func: Callable,
):
    """
    Input:
    node: RaireNode    -  A node in the tree of alternate election outcomes.
                         Starting point of dive to a leaf.

    contest: Contest   -  Contest being audited.

    cvrs: List of CVR  -  Details of reported ballots for this contest.

    neb_matrix         -  |Candidates| x |Candidates| dictionary where
                          neb_matrix[c1][c2] returns a NEBAssertion stating
                          that c1 cannot be eliminated before c2 (if one
                          exists) and None otherwise.

    asn_func: Callable -  Function that takes an assertion margin and
                          returns an estimate of how "difficult" it will
                          be to audit that assertion.

    Output:
    Returns the difficulty estimate of the least-difficult-to-audit
    assertion that can be used to rule out at least one of the branches
    starting at the input 'node'.
    """

    rem_cands = [c for c in contest.candidates if not c in node.tail]
    next_cand = rem_cands[0]

    newn = RaireNode([next_cand] + node.tail)
    newn.expandable = len(newn.tail) < len(contest.candidates)

    # Assign a 'best ancestor' to the new node.
    if node.best_ancestor and node.best_ancestor.estimate <= node.estimate:
        newn.best_ancestor = node.best_ancestor
    else:
        newn.best_ancestor = node

    find_best_audit(contest, ballots, neb_matrix, newn, asn_func)
    if not newn.expandable:
        if newn.estimate == np.inf and newn.best_ancestor.estimate == np.inf:
            # Audit is not possible: We have found a leaf and cannot
            # form an assertion to rule out it or any of its ancestors.
            return np.inf

        return min(newn.estimate, newn.best_ancestor.estimate)

    else:
        return perform_dive(newn, contest, ballots, neb_matrix, asn_func)
