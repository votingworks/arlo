# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots["test_contests_round_status 1"] = [
    {
        "currentRoundStatus": {"isRiskLimitMet": None, "numBallotsSampled": 343},
        "name": "Contest 1",
    },
    {
        "currentRoundStatus": {"isRiskLimitMet": None, "numBallotsSampled": 0},
        "name": "Contest 2",
    },
    {
        "currentRoundStatus": {"isRiskLimitMet": None, "numBallotsSampled": 240},
        "name": "Contest 3",
    },
]
