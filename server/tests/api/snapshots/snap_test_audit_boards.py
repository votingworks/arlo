# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots["test_audit_boards_create_one 1"] = 81

snapshots["test_audit_boards_list_one 1"] = [
    {
        "currentRoundStatus": {"numAuditedBallots": 0, "numSampledBallots": 75},
        "name": "Audit Board #1",
    }
]

snapshots["test_audit_boards_list_one 2"] = [
    {
        "currentRoundStatus": {"numAuditedBallots": 10, "numSampledBallots": 75},
        "name": "Audit Board #1",
    }
]

snapshots["test_audit_boards_list_one 3"] = [
    {
        "currentRoundStatus": {"numAuditedBallots": 75, "numSampledBallots": 75},
        "name": "Audit Board #1",
    }
]

snapshots["test_audit_boards_create_two 1"] = 81

snapshots["test_audit_boards_list_two 1"] = [
    {
        "currentRoundStatus": {"numAuditedBallots": 0, "numSampledBallots": 50},
        "name": "Audit Board #1",
    },
    {
        "currentRoundStatus": {"numAuditedBallots": 0, "numSampledBallots": 25},
        "name": "Audit Board #2",
    },
]

snapshots["test_audit_boards_list_two 2"] = [
    {
        "currentRoundStatus": {"numAuditedBallots": 10, "numSampledBallots": 50},
        "name": "Audit Board #1",
    },
    {
        "currentRoundStatus": {"numAuditedBallots": 20, "numSampledBallots": 25},
        "name": "Audit Board #2",
    },
]

snapshots["test_audit_boards_list_two 3"] = [
    {
        "currentRoundStatus": {"numAuditedBallots": 50, "numSampledBallots": 50},
        "name": "Audit Board #1",
    },
    {
        "currentRoundStatus": {"numAuditedBallots": 20, "numSampledBallots": 25},
        "name": "Audit Board #2",
    },
]

snapshots["test_audit_boards_create_round_2 1"] = 257

snapshots["test_audit_boards_list_round_2 1"] = [
    {
        "currentRoundStatus": {"numAuditedBallots": 21, "numSampledBallots": 137},
        "name": "Audit Board #1",
    },
    {
        "currentRoundStatus": {"numAuditedBallots": 5, "numSampledBallots": 43},
        "name": "Audit Board #2",
    },
    {
        "currentRoundStatus": {"numAuditedBallots": 3, "numSampledBallots": 36},
        "name": "Audit Board #3",
    },
]
