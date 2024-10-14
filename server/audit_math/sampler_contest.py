"""
A Module containing the Contest class, which encapsulates useful info for RLA
computations.
"""

import operator
from typing import Dict, Optional, TypedDict


def from_db_contest(db_contest):
    """
    Builds sampler_contest object from the database

    Inputs:
        db_contest - a contest object as defined in server/models.py

    Outputs:
        Contest - A contest object
    """
    name = db_contest.id
    info_dict = {
        "ballots": db_contest.total_ballots_cast,
        "numWinners": db_contest.num_winners,
        "votesAllowed": db_contest.votes_allowed,
    }

    # Initialize the choices in this contest and how many votes each received
    for choice in db_contest.choices:
        info_dict[choice.id] = choice.num_votes

    return Contest(name, info_dict)


class Contest:
    """
    An object for storing per-contest information, including total number of
    ballots, the candidates and vote totals, and the number of winners.
    """

    candidates: Dict[str, int]  # Dict mapping candidates to their vote totals
    num_winners: int  # How many winners this contest had
    votes_allowed: int  # How many voters are allowed in this contest
    ballots: int  # The total number of ballots cast in this contest
    name: str  # The name of the contest

    winners: Dict[str, int]  # List of all the winners
    losers: Dict[str, int]  # List of all the losers

    diluted_margin: float  # The smallest diluted margin in this contest
    margins: Dict[str, Dict]  # Dict of the margins for this contest

    def __init__(self, name: str, contest_info_dict: Dict[str, int]):
        """
        Initializes the contest info from a dict of the form:
            {
                candidate1: votes,
                candidate2: votes,
                ...
                'ballots': ballots,
                'winners': winners
            }

        """
        self.name = name

        self.ballots = contest_info_dict["ballots"]
        self.num_winners = contest_info_dict["numWinners"]
        self.votes_allowed = contest_info_dict["votesAllowed"]

        self.candidates = {}

        self.winners = {}
        self.losers = {}

        for cand in contest_info_dict:
            if cand in ["ballots", "numWinners", "votesAllowed"]:
                continue

            self.candidates[cand] = contest_info_dict[cand]

        # pylint: disable=pointless-string-statement
        """
        Initialize a dictionary of diluted margin info:
        {
            contest: {
                'winners': {
                    winner1: {
                              'p_w': p_w,     # Proportion of ballots for this winner
                              's_w': 's_w'    # proportion of votes for this winner
                              'swl': {      # fraction of votes for w among (w, l)
                                    'loser1':  s_w/(s_w + s_l1),
                                    ...,
                                    'losern':  s_w/(s_w + s_ln)
                                }
                              },
                    ...,
                    winnern: {...} ]
                'losers': {
                    loser1: {
                              'p_l': p_l,     # Proportion of votes for this loser
                              's_l': s_l,     # Proportion of ballots for this loser
                              },
                    ...,
                    losern: {...} ]

            }
        }

        """
        self.margins = {"winners": {}, "losers": {}}

        cand_vec = sorted(
            self.candidates.items(),
            key=operator.itemgetter(1),
            reverse=True,
        )

        v_wl = 0

        for i, choice in enumerate(cand_vec):
            v_wl += choice[1]
            if i < self.num_winners:
                self.winners[choice[0]] = choice[1]

            else:
                self.losers[choice[0]] = choice[1]

        # pylint: disable=consider-using-dict-items
        for loser in self.losers:
            self.margins["losers"][loser] = {
                "p_l": self.losers[loser] / self.ballots,
                "s_l": self.losers[loser] / v_wl,
            }

        min_margin = self.ballots

        # pylint: disable=consider-using-dict-items
        for winner in self.winners:
            s_w = self.winners[winner] / v_wl

            swl = {}
            for loser in self.losers:
                s_l = self.margins["losers"][loser]["s_l"]
                swl[loser] = s_w / (s_w + s_l)

                # Find the smallest margin, in ballots
                if self.winners[winner] - self.losers[loser] < min_margin:
                    min_margin = self.winners[winner] - self.losers[loser]

            self.margins["winners"][winner] = {
                "p_w": self.winners[winner] / self.ballots,
                "s_w": s_w,
                "swl": swl,
            }

        if self.losers:
            self.diluted_margin = float(min_margin) / self.ballots
        else:
            self.diluted_margin = -1.0

    def __repr__(self) -> str:
        """
        Generates a string representation of this object, for debugging.
        """
        return f"Contest({self.name}): numWinners: {self.num_winners}, votesAllowed: {self.votes_allowed}, total ballots: {self.ballots}, candidates: {self.candidates}"


# CVR: { contest_id: { choice_id: "0" | "1" | "o" | "u" }}
# Note: "o" and "u" are special cases for ES&S CVR overvotes and undervotes
# CVRS: { ballot_id: CVR }
CVR = Dict[str, Dict[str, str]]
CVRS = Dict[str, Optional[CVR]]


class SampleCVR(TypedDict):
    times_sampled: int
    cvr: Optional[CVR]


SAMPLECVRS = Dict[str, SampleCVR]
