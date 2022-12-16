import abc
from abc import ABC, abstractmethod
from r2b2.contest import Contest as Contest, PairwiseContest as PairwiseContest
from typing import Any, Dict, List

class PairwiseAudit:
    sub_contest: PairwiseContest
    min_sample_size: int
    risk_schedule: List[float]
    stopping_prob_schedule: List[float]
    pvalue_schedule: List[float]
    distribution_null: List[float]
    distribution_reported_tally: List[float]
    min_winner_ballots: List[int]
    stopped: bool
    def __init__(self, sub_contest: PairwiseContest) -> None: ...
    def get_pair_str(self): ...

class Audit(ABC, metaclass=abc.ABCMeta):
    alpha: float
    beta: float
    max_fraction_to_draw: float
    replacement: bool
    selection_ordered: bool
    rounds: List[int]
    sample_winner_ballots: List[int]
    pvalue_schedule: List[float]
    contest: Contest
    sample_ballots: Dict[str, List[int]]
    sub_audits: Dict[str, PairwiseAudit]
    stopped: bool
    def __init__(
        self,
        alpha: float,
        beta: float,
        max_fraction_to_draw: float,
        replacement: bool,
        contest: Contest,
    ) -> None: ...
    def current_dist_null(self) -> None: ...
    def current_dist_reported(self) -> None: ...
    def truncate_dist_null(self) -> None: ...
    def truncate_dist_reported(self) -> None: ...
    def asn(self, pair: str) -> Any: ...
    def execute_round(
        self, sample_size: int, sample: dict, verbose: bool = ...
    ) -> bool: ...
    def run(self, verbose: bool = ...) -> Any: ...
    @abstractmethod
    def get_min_sample_size(self, sub_audit: PairwiseAudit) -> Any: ...
    @abstractmethod
    def next_sample_size(self, *args: Any, **kwargs: Any) -> Any: ...
    def stopping_condition(self, verbose: bool = ...) -> bool: ...
    @abstractmethod
    def stopping_condition_pairwise(self, pair: str, verbose: bool = ...) -> bool: ...
    def next_min_winner_ballots(self, verbose: bool = ...) -> Any: ...
    @abstractmethod
    def next_min_winner_ballots_pairwise(self, sub_audit: PairwiseAudit) -> int: ...
    @abstractmethod
    def compute_min_winner_ballots(
        self, sub_audit: PairwiseAudit, progress: bool = ..., *args: Any, **kwargs: Any
    ) -> Any: ...
    @abstractmethod
    def compute_all_min_winner_ballots(
        self, sub_audit: PairwiseAudit, progress: bool = ..., *args: Any, **kwargs: Any
    ) -> Any: ...
    @abstractmethod
    def compute_risk(
        self, sub_audit: PairwiseAudit, *args: Any, **kwargs: Any
    ) -> Any: ...
    @abstractmethod
    def get_risk_level(self, *args: Any, **kwargs: Any) -> Any: ...
