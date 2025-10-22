from typing import Literal, NamedTuple, TypedDict


class SampleSizeOption(TypedDict):
    type: Literal["ASN"] | Literal["all-ballots"] | None
    size: int
    prob: float | None


RoundInfo = NamedTuple("RoundInfo", [("round_id", str), ("round_size", int)])

# { round_id: { choice_id: num_votes }}
BALLOT_POLLING_SAMPLE_RESULTS = dict[str, dict[str, int]]

# { round_num: [ round_id, round_size ]}
BALLOT_POLLING_ROUND_SIZES = dict[int, RoundInfo]
