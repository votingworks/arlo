from typing import Dict, Literal, NamedTuple, Optional, TypedDict


class SampleSizeOption(TypedDict):
    type: Optional[Literal["ASN", "all-ballots"]]
    size: int
    prob: Optional[float]


RoundInfo = NamedTuple("RoundInfo", [("round_id", str), ("round_size", int)])

# { round_id: { choice_id: num_votes }}
BALLOT_POLLING_SAMPLE_RESULTS = Dict[str, Dict[str, int]]

# { round_num: [ round_id, round_size ]}
BALLOT_POLLING_ROUND_SIZES = Dict[int, RoundInfo]
