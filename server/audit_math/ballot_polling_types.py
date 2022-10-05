from typing import Literal, Optional, TypedDict


class SampleSizeOption(TypedDict):
    type: Optional[Literal["ASN", "all-ballots"]]
    size: int
    prob: Optional[float]
