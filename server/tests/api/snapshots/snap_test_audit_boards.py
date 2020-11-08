# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots["test_audit_boards_create_one 1"] = 60

snapshots["test_audit_boards_create_two 1"] = 60

snapshots["test_audit_boards_list_one 1"] = [
    {
        "currentRoundStatus": {"numAuditedBallots": 0, "numSampledBallots": 59},
        "name": "Audit Board #1",
    }
]

snapshots["test_audit_boards_list_one 2"] = [
    {
        "currentRoundStatus": {"numAuditedBallots": 10, "numSampledBallots": 59},
        "name": "Audit Board #1",
    }
]

snapshots["test_audit_boards_list_one 3"] = [
    {
        "currentRoundStatus": {"numAuditedBallots": 59, "numSampledBallots": 59},
        "name": "Audit Board #1",
    }
]

snapshots["test_audit_boards_list_two 1"] = [
    {
        "currentRoundStatus": {"numAuditedBallots": 0, "numSampledBallots": 37},
        "name": "Audit Board #1",
    },
    {
        "currentRoundStatus": {"numAuditedBallots": 0, "numSampledBallots": 22},
        "name": "Audit Board #2",
    },
]

snapshots["test_audit_boards_list_two 2"] = [
    {
        "currentRoundStatus": {"numAuditedBallots": 10, "numSampledBallots": 37},
        "name": "Audit Board #1",
    },
    {
        "currentRoundStatus": {"numAuditedBallots": 20, "numSampledBallots": 22},
        "name": "Audit Board #2",
    },
]

snapshots["test_audit_boards_list_two 3"] = [
    {
        "currentRoundStatus": {"numAuditedBallots": 37, "numSampledBallots": 37},
        "name": "Audit Board #1",
    },
    {
        "currentRoundStatus": {"numAuditedBallots": 20, "numSampledBallots": 22},
        "name": "Audit Board #2",
    },
]
