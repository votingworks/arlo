from r2b2.minerva2 import Minerva2 as Minerva2
from r2b2.simulator import Simulation as Simulation, histogram as histogram
from typing import Any, List, Optional, Tuple

class Minerva2OneRoundRisk(Simulation):
    sample_size: int
    total_relevant_ballots: int
    vote_dist: List[Tuple[str, int]]
    audit: Minerva2
    contest_ballots: Any = ...
    def __init__(
        self,
        alpha: Any,
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

class Minerva2OneRoundStoppingProb(Simulation):
    sample_size: int
    total_relevant_ballots: int
    vote_dist: List[Tuple[str, int]]
    audit: Minerva2
    contest_ballots: Any = ...
    def __init__(
        self,
        alpha: Any,
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

class Minerva2OneRoundAlteredMargin(Simulation):
    underlying_margin: float
    sample_size: int
    total_relevant_ballots: int
    vote_dist: List[Tuple[str, int]]
    audit: Minerva2
    contest_ballots: Any = ...
    def __init__(
        self,
        alpha: Any,
        reported: Any,
        underlying: Any,
        underlying_margin: Any,
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

class Minerva2MultiRoundStoppingProb(Simulation):
    sample_sprob: float
    sample_size: int
    sample_mult: float
    max_rounds: int
    total_relevant_ballots: int
    vote_dist: List[Tuple[str, int]]
    audit: Minerva2
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

class Minerva2MultiRoundRisk(Simulation):
    sample_sprob: float
    sample_size: int
    sample_mult: float
    max_rounds: int
    total_relevant_ballots: int
    vote_dist: List[Tuple[str, int]]
    audit: Minerva2
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

class Minerva2RandomMultiRoundRisk(Simulation):
    sample_size: int
    max_rounds: int
    total_relevant_ballots: int
    vote_dist: List[Tuple[str, int]]
    audit: Minerva2
    contest_ballots: Any = ...
    def __init__(
        self,
        alpha: Any,
        reported: Any,
        sample_size: Any,
        max_rounds: Any,
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

class Minerva2RandomMultiRoundStoppingProb(Simulation):
    sample_size: int
    max_rounds: int
    total_relevant_ballots: int
    vote_dist: List[Tuple[str, int]]
    audit: Minerva2
    contest_ballots: Any = ...
    def __init__(
        self,
        alpha: Any,
        reported: Any,
        sample_size: Any,
        max_rounds: Any,
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

class Minerva2MultiRoundAlteredMargin(Simulation):
    underlying_margin: float
    sample_size: int
    max_rounds: int
    total_relevant_ballots: int
    vote_dist: List[Tuple[str, int]]
    audit: Minerva2
    contest_ballots: Any = ...
    def __init__(
        self,
        alpha: Any,
        reported: Any,
        underlying: Any,
        underlying_margin: Any,
        sample_size: Any,
        max_rounds: Any,
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
