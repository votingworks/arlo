from typing import Dict, Literal, Optional, Tuple, TypedDict


class SampleSizeOption(TypedDict):
    type: Optional[Literal["ASN", "all-ballots"]]
    size: int
    prob: Optional[float]


# { round_id: { choice_id: num_votes }}
BALLOT_POLLING_SAMPLE_RESULTS = Dict[  # pylint: disable=invalid-name
    str, Dict[str, int]
]

# { round_num: [ round_id, round_size ]}
BALLOT_POLLING_ROUND_SIZES = Dict[int, Tuple[str, int]]  # pylint: disable=invalid-name
