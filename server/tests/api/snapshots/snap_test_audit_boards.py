# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots["test_audit_boards_create_two 1"] = 80

snapshots["test_audit_boards_create_one 1"] = 80

snapshots["test_audit_boards_create_round_2 1"] = 248

snapshots["test_audit_boards_list_one 1"] = [
    {
        "currentRoundStatus": {"numAuditedBallots": 0, "numSampledBallots": 76},
        "name": "Audit Board #1",
    }
]

snapshots["test_audit_boards_list_one 2"] = [
    {
        "currentRoundStatus": {"numAuditedBallots": 10, "numSampledBallots": 76},
        "name": "Audit Board #1",
    }
]

snapshots["test_audit_boards_list_one 3"] = [
    {
        "currentRoundStatus": {"numAuditedBallots": 76, "numSampledBallots": 76},
        "name": "Audit Board #1",
    }
]

snapshots["test_audit_boards_list_two 1"] = [
    {
        "currentRoundStatus": {"numAuditedBallots": 0, "numSampledBallots": 46},
        "name": "Audit Board #1",
    },
    {
        "currentRoundStatus": {"numAuditedBallots": 0, "numSampledBallots": 30},
        "name": "Audit Board #2",
    },
]

snapshots["test_audit_boards_list_two 2"] = [
    {
        "currentRoundStatus": {"numAuditedBallots": 10, "numSampledBallots": 46},
        "name": "Audit Board #1",
    },
    {
        "currentRoundStatus": {"numAuditedBallots": 20, "numSampledBallots": 30},
        "name": "Audit Board #2",
    },
]

snapshots["test_audit_boards_list_two 3"] = [
    {
        "currentRoundStatus": {"numAuditedBallots": 46, "numSampledBallots": 46},
        "name": "Audit Board #1",
    },
    {
        "currentRoundStatus": {"numAuditedBallots": 20, "numSampledBallots": 30},
        "name": "Audit Board #2",
    },
]

snapshots["test_audit_boards_list_round_2 1"] = [
    {
        "currentRoundStatus": {"numAuditedBallots": 16, "numSampledBallots": 122},
        "name": "Audit Board #1",
    },
    {
        "currentRoundStatus": {"numAuditedBallots": 6, "numSampledBallots": 39},
        "name": "Audit Board #2",
    },
    {
        "currentRoundStatus": {"numAuditedBallots": 6, "numSampledBallots": 40},
        "name": "Audit Board #3",
    },
]
