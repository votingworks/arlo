from r2b2.simulator import Simulation as Simulation, histogram as histogram
from r2b2.so_bravo import SO_BRAVO as SO_BRAVO
from typing import Any, List, Optional, Tuple

class SO_BRAVOMultiRoundStoppingProb(Simulation):
    sample_sprob: float
    sample_size: int
    sample_mult: float
    max_rounds: int
    total_relevant_ballots: int
    vote_dist: List[Tuple[str, int]]
    audit: SO_BRAVO
    contest_ballots: Any = ...
    def __init__(
        self,
        alpha: Any,
        reported: Any,
        max_rounds: Any,
        sample_size: Optional[Any] = ...,
        sample_mult: Optional[Any] = ...,
        sample_sprob: Optional[Any] = ...,
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

class SO_BRAVOMultiRoundRisk(Simulation):
    sample_sprob: float
    sample_size: int
    sample_mult: float
    max_rounds: int
    total_relevant_ballots: int
    vote_dist: List[Tuple[str, int]]
    audit: SO_BRAVO
    contest_ballots: Any = ...
    def __init__(
        self,
        alpha: Any,
        reported: Any,
        max_rounds: Any,
        sample_size: Optional[Any] = ...,
        sample_mult: Optional[Any] = ...,
        sample_sprob: Optional[Any] = ...,
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
