from collections import namedtuple
from typing import Dict, Literal, Optional, TypedDict


class SampleSizeOption(TypedDict):
    type: Optional[Literal["ASN", "all-ballots"]]
    size: int
    prob: Optional[float]


RoundInfo = namedtuple("RoundInfo", ["round_id", "round_size"])

# { round_id: { choice_id: num_votes }}
BALLOT_POLLING_SAMPLE_RESULTS = Dict[  # pylint: disable=invalid-name
    str, Dict[str, int]
]

# { round_num: [ round_id, round_size ]}
BALLOT_POLLING_ROUND_SIZES = Dict[int, RoundInfo]  # pylint: disable=invalid-name
