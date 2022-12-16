from r2b2.contest import Contest as Contest
from typing import Dict

class Election:
    name: str
    total_ballots: int
    contests: Dict[str, Contest]
    def __init__(
        self, name: str, total_ballots: int, contests: Dict[str, Contest]
    ) -> None: ...
    def add_contest(self) -> None: ...
