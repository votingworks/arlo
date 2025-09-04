import abc
from abc import ABC, abstractmethod
from r2b2.contest import Contest as Contest
from typing import Any, List

class DBInterface:
    client: Any = ...
    db: Any = ...
    def __init__(
        self,
        host: str = ...,
        port: int = ...,
        name: str = ...,
        user: str = ...,
        pwd: str = ...,
    ) -> None: ...
    def audit_lookup(
        self, audit_type: str, alpha: float, qapp: dict = ..., *args: Any, **kwargs: Any
    ) -> Any: ...
    def contest_lookup(
        self, contest: Contest, qapp: dict = ..., *args: Any, **kwargs: Any
    ) -> Any: ...
    def simulation_lookup(
        self,
        audit: Any,
        reported: Any,
        underlying: Any,
        invalid: Any,
        qapp: dict = ...,
        *args: Any,
        **kwargs: Any,
    ) -> Any: ...
    def trial_lookup(self, sim_id: Any, *args: Any, **kwargs: Any): ...
    def write_trial(self, entry: Any) -> None: ...
    def update_analysis(self, sim_id: Any, entry: Any) -> None: ...

class Simulation(ABC, metaclass=abc.ABCMeta):
    db_mode: bool
    db: DBInterface
    audit_type: str
    alpha: float
    audit_id: str
    reported: Contest
    reported_id: str
    underlying: str
    invalid: bool
    sim_id: str
    trials: List
    def __init__(
        self,
        audit_type: str,
        alpha: float,
        reported: Contest,
        underlying: Any,
        invalid: bool,
        db_mode: Any = ...,
        db_host: Any = ...,
        db_port: Any = ...,
        db_name: Any = ...,
        user: Any = ...,
        pwd: Any = ...,
        *args: Any,
        **kwargs: Any,
    ) -> None: ...
    def run(self, n: int) -> Any: ...
    def get_seed(self): ...
    def output(self, fd: str = ...) -> Any: ...
    def output_audit(self): ...
    @abstractmethod
    def trial(self, seed: Any) -> Any: ...
    @abstractmethod
    def analyze(self, *args: Any, **kwargs: Any) -> Any: ...

def histogram(values: List, xlabel: str, bins: Any = ...) -> Any: ...
