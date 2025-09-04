from enum import Enum
from typing import Dict, List

class ContestType(Enum):
    PLURALITY: int = ...
    MAJORITY: int = ...

class PairwiseContest:
    contest_ballots: int
    reported_winner: str
    reported_loser: str
    reported_winner_ballots: int
    reported_loser_ballots: int
    winner_prop: float
    def __init__(
        self,
        reported_winner: str,
        reported_loser: str,
        reported_winner_ballots: int,
        reported_loser_ballots: int,
    ) -> None: ...

class Contest:
    contest_ballots: int
    irrelevant_ballots: int
    candidates: List[str]
    num_candidates: int
    num_winners: int
    reported_winners: List[str]
    contest_type: ContestType
    tally: Dict[str, int]
    sub_contests: List[PairwiseContest]
    def __init__(
        self,
        contest_ballots: int,
        tally: Dict[str, int],
        num_winners: int,
        reported_winners: List[str],
        contest_type: ContestType,
    ) -> None: ...
    def to_json(self): ...
