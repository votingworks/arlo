import numpy as np
from r2b2.audit import Audit as Audit, PairwiseAudit as PairwiseAudit
from r2b2.contest import Contest as Contest
from typing import Any, List

class BayesianRLA(Audit):
    prior: np.ndarray
    def __init__(
        self,
        alpha: float,
        max_fraction_to_draw: float,
        contest: Contest,
        reported_winner: str = ...,
    ) -> None: ...
    def get_min_sample_size(self, sub_audit: PairwiseAudit) -> Any: ...
    def stopping_condition_pairwise(self, pair: str, verbose: bool = ...) -> bool: ...
    def next_min_winner_ballots_pairwise(
        self, sub_audit: PairwiseAudit, sample_size: int = ...
    ) -> int: ...
    def compute_priors(self) -> np.ndarray: ...
    def compute_risk(
        self,
        sub_audit: PairwiseAudit,
        votes_for_winner: int = ...,
        current_round: int = ...,
        *args: Any,
        **kwargs: Any,
    ) -> float: ...
    def next_sample_size(self) -> None: ...
    rounds: Any = ...
    def compute_min_winner_ballots(
        self,
        sub_audit: PairwiseAudit,
        rounds: List[int],
        progress: bool = ...,
        *args: Any,
        **kwargs: Any,
    ) -> Any: ...
    def compute_all_min_winner_ballots(
        self,
        sub_audit: PairwiseAudit,
        max_sample_size: int = ...,
        progress: bool = ...,
        *args: Any,
        **kwargs: Any,
    ) -> Any: ...
    def get_risk_level(self, *args: Any, **kwargs: Any) -> None: ...
