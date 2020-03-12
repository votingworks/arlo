"""
A Module containing the Contest class, which encapsulates useful info for RLA
computations.
"""
from typing import Dict, Optional, Tuple, List, cast
import operator


def from_db_contest(db_contest):
    name = db_contest.id
    info_dict = {
        "ballots": db_contest.total_ballots_cast,
        "numWinners": db_contest.num_winners,
        "votesAllowed": db_contest.votes_allowed,
    }

    for choice in db_contest.choices:
        info_dict[choice.id] = choice.num_votes

    return Contest(name, info_dict)


class Contest:
    """
    An object for storing per-contest information, including total number of
    ballots, the candidates and vote totals, and the number of winners. 
    """

    candidates: Dict[str, int]  # Dict mapping candidates to their vote totals
    numWinners: int  # How many winners this contest had
    votesAllowed: int  # How many voters are allowed in this contest
    ballots: int  # The total number of ballots cast in this contest
    name: str  # The name of the contest

    winners: List[str]  # List of all the winners
    losers: List[str]  # List of all the losers

    margins: Dict[str, Dict]  # Dict of the margins for this contest

    def __init__(self, name, contest_info_dict):
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
        self.numWinners = contest_info_dict["numWinners"]
        self.votesAllowed = contest_info_dict["votesAllowed"]

        self.candidates = {}

        self.winners = []
        self.losers = []

        for cand in contest_info_dict:
            if cand in ["ballots", "numWinners", "votesAllowed"]:
                continue

            self.candidates[cand] = contest_info_dict[cand]
        """
        Output:
            margins - dictionary of diluted margin info:
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
            [(cand, self.candidates[cand]) for cand in self.candidates],
            key=operator.itemgetter(1),
            reverse=True,
        )

        self.winners = cand_vec[: self.numWinners]
        self.losers = cand_vec[self.numWinners :]

        v_wl = sum([c[1] for c in self.winners + self.losers])

        for loser in self.losers:
            self.margins["losers"][loser[0]] = {
                "p_l": loser[1] / self.ballots,
                "s_l": loser[1] / v_wl,
            }

        for winner in self.winners:
            s_w = winner[1] / v_wl

            swl = {}
            for loser in self.margins["losers"]:
                s_l = self.margins["losers"][loser]["s_l"]
                swl[loser] = s_w / (s_w + s_l)

            self.margins["winners"][winner[0]] = {
                "p_w": winner[1] / self.ballots,
                "s_w": s_w,
                "swl": swl,
            }

    def __repr__(self):
        return "Contest({}): numWinners: {}, votesAllowed: {}, total ballots: {}, candidates: {}".format(
            self.name, self.numWinners, self.votesAllowed, self.ballots, self.candidates
        )
