import click
from r2b2.athena import Athena as Athena
from r2b2.audit import Audit as Audit
from r2b2.contest import Contest as Contest, ContestType as ContestType
from r2b2.election import Election as Election
from r2b2.eor_bravo import EOR_BRAVO as EOR_BRAVO
from r2b2.minerva import Minerva as Minerva
from r2b2.minerva2 import Minerva2 as Minerva2
from r2b2.so_bravo import SO_BRAVO as SO_BRAVO
from r2b2.tests import util as util
from typing import Any

class IntList(click.ParamType):
    name: str = ...
    def convert(self, value: Any, param: Any, ctx: Any): ...

INT_LIST: Any
audit_types: Any
contest_types: Any

def cli() -> None: ...
def interactive(
    election_mode: Any,
    election_file: Any,
    contest_file: Any,
    audit_type: Any,
    risk_limit: Any,
    max_fraction_to_draw: Any,
    verbose: Any,
) -> None: ...
def bulk(
    audit_type: Any,
    risk_limit: Any,
    max_fraction_to_draw: Any,
    contest_file: Any,
    output: Any,
    round_list: Any,
    full_audit_limit: Any,
    pair: Any,
    verbose: Any,
) -> None: ...
def template(style: Any, output: Any) -> None: ...
def input_audit(
    contest: Contest,
    alpha: float = ...,
    max_fraction_to_draw: float = ...,
    audit_type: str = ...,
    delta: float = ...,
) -> Audit: ...
def input_contest() -> Contest: ...
def input_election() -> Election: ...
def input_warning(msg: Any) -> None: ...
