# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots["test_jurisdictions_status_round_1_no_audit_boards 1"] = [
    {
        "currentRoundStatus": {
            "numSamples": 80,
            "numSamplesAudited": 0,
            "numUnique": 76,
            "numUniqueAudited": 0,
            "status": "NOT_STARTED",
        },
        "name": "J1",
    },
    {
        "currentRoundStatus": {
            "numSamples": 39,
            "numSamplesAudited": 0,
            "numUnique": 36,
            "numUniqueAudited": 0,
            "status": "NOT_STARTED",
        },
        "name": "J2",
    },
    {
        "currentRoundStatus": {
            "numSamples": 0,
            "numSamplesAudited": 0,
            "numUnique": 0,
            "numUniqueAudited": 0,
            "status": "COMPLETE",
        },
        "name": "J3",
    },
]

snapshots["test_jurisdictions_status_round_1_with_audit_boards 1"] = [
    {
        "currentRoundStatus": {
            "numSamples": 80,
            "numSamplesAudited": 0,
            "numUnique": 76,
            "numUniqueAudited": 0,
            "status": "IN_PROGRESS",
        },
        "name": "J1",
    },
    {
        "currentRoundStatus": {
            "numSamples": 39,
            "numSamplesAudited": 0,
            "numUnique": 36,
            "numUniqueAudited": 0,
            "status": "NOT_STARTED",
        },
        "name": "J2",
    },
    {
        "currentRoundStatus": {
            "numSamples": 0,
            "numSamplesAudited": 0,
            "numUnique": 0,
            "numUniqueAudited": 0,
            "status": "COMPLETE",
        },
        "name": "J3",
    },
]

snapshots["test_jurisdictions_status_round_1_with_audit_boards 2"] = {
    "numSamples": 80,
    "numSamplesAudited": 49,
    "numUnique": 76,
    "numUniqueAudited": 46,
    "status": "IN_PROGRESS",
}

snapshots["test_jurisdictions_status_round_1_with_audit_boards 3"] = {
    "numSamples": 80,
    "numSamplesAudited": 80,
    "numUnique": 76,
    "numUniqueAudited": 76,
    "status": "COMPLETE",
}

snapshots["test_jurisdictions_round_status_offline 1"] = {
    "numSamples": 80,
    "numSamplesAudited": 0,
    "numUnique": 76,
    "numUniqueAudited": 0,
    "status": "NOT_STARTED",
}

snapshots["test_jurisdictions_round_status_offline 2"] = {
    "numSamples": 80,
    "numSamplesAudited": 0,
    "numUnique": 76,
    "numUniqueAudited": 0,
    "status": "IN_PROGRESS",
}

snapshots["test_jurisdictions_round_status_offline 3"] = {
    "numSamples": 80,
    "numSamplesAudited": 80,
    "numUnique": 76,
    "numUniqueAudited": 76,
    "status": "COMPLETE",
}
