from r2b2.athena import Athena as Athena
from r2b2.simulator import Simulation as Simulation, histogram as histogram
from typing import Any, List, Tuple

class AthenaOneRoundRisk(Simulation):
    delta: float
    sample_size: int
    total_relevant_ballots: int
    vote_dist: List[Tuple[str, int]]
    audit: Athena
    contest_ballots: Any = ...
    def __init__(
        self,
        alpha: Any,
        delta: Any,
        reported: Any,
        sample_size: Any,
        db_mode: bool = ...,
        db_host: str = ...,
        db_name: str = ...,
        db_port: int = ...,
        user: str = ...,
        pwd: str = ...,
        *args: Any,
        **kwargs: Any
    ): ...
    def trial(self, seed: Any): ...
    def analyze(self, verbose: bool = ..., hist: bool = ...) -> Any: ...

class AthenaOneRoundStoppingProb(Simulation):
    delta: float
    sample_size: int
    total_relevant_ballots: int
    vote_dist: List[Tuple[str, int]]
    audit: Athena
    contest_ballots: Any = ...
    def __init__(
        self,
        alpha: Any,
        delta: Any,
        reported: Any,
        sample_size: Any,
        db_mode: bool = ...,
        db_host: str = ...,
        db_name: str = ...,
        db_port: int = ...,
        user: str = ...,
        pwd: str = ...,
        *args: Any,
        **kwargs: Any
    ): ...
    def trial(self, seed: Any): ...
    def analyze(self, verbose: bool = ..., hist: bool = ...) -> Any: ...
