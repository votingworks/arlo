# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots["test_jurisdictions_status_round_1_no_audit_boards 1"] = [
    {
        "currentRoundStatus": {
            "numSamples": 81,
            "numSamplesAudited": 0,
            "numUnique": 75,
            "numUniqueAudited": 0,
            "status": "NOT_STARTED",
        },
        "name": "J1",
    },
    {
        "currentRoundStatus": {
            "numSamples": 38,
            "numSamplesAudited": 0,
            "numUnique": 35,
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
            "numSamples": 81,
            "numSamplesAudited": 0,
            "numUnique": 75,
            "numUniqueAudited": 0,
            "status": "IN_PROGRESS",
        },
        "name": "J1",
    },
    {
        "currentRoundStatus": {
            "numSamples": 38,
            "numSamplesAudited": 0,
            "numUnique": 35,
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
    "numSamples": 81,
    "numSamplesAudited": 54,
    "numUnique": 75,
    "numUniqueAudited": 50,
    "status": "IN_PROGRESS",
}

snapshots["test_jurisdictions_status_round_1_with_audit_boards 3"] = {
    "numSamples": 81,
    "numSamplesAudited": 81,
    "numUnique": 75,
    "numUniqueAudited": 75,
    "status": "COMPLETE",
}

snapshots["test_jurisdictions_round_status_offline 1"] = {
    "numSamples": 81,
    "numSamplesAudited": 0,
    "numUnique": 75,
    "numUniqueAudited": 0,
    "status": "NOT_STARTED",
}

snapshots["test_jurisdictions_round_status_offline 2"] = {
    "numSamples": 81,
    "numSamplesAudited": 0,
    "numUnique": 75,
    "numUniqueAudited": 0,
    "status": "IN_PROGRESS",
}

snapshots["test_jurisdictions_round_status_offline 3"] = {
    "numSamples": 81,
    "numSamplesAudited": 81,
    "numUnique": 75,
    "numUniqueAudited": 75,
    "status": "COMPLETE",
}
