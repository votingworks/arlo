from r2b2.contest import Contest as Contest, ContestType as ContestType
from r2b2.election import Election as Election
from typing import Any, Optional

def generate_contest(size: Any): ...
def generate_election(max_size: Any, max_contests: Optional[Any] = ...): ...
def parse_contest_list(json_file: Any): ...
def parse_contest(json_file: Any): ...
def parse_election(json_file: Any): ...