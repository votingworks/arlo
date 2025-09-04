from r2b2.simulator import Simulation as Simulation, histogram as histogram
from typing import Any, List, Tuple

class FZMinervaOneRoundRisk(Simulation):
    sample_size: int
    total_relevant_ballots: int
    vote_dist: List[Tuple[str, int]]
    election_file: str
    reported_name: str
    def __init__(
        self,
        alpha: Any,
        reported: Any,
        sample_size: Any,
        election_file: Any,
        reported_name: Any,
        db_mode: bool = ...,
        db_host: str = ...,
        db_name: str = ...,
        db_port: int = ...,
        *args: Any,
        **kwargs: Any
    ): ...
    def trial(self, seed: Any): ...
    def analyze(self) -> None: ...
