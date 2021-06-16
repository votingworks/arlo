# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots["test_slack_worker_message_format 1"] = {
    "blocks": [
        {
            "text": {
                "text": "*test_user@example.com created an audit: <http://localhost:3000/support/audits/test_election_id|Test Audit>* (Ballot Comparison)",
                "type": "mrkdwn",
            },
            "type": "section",
        },
        {
            "elements": [
                {
                    "text": ":flag-us: <http://localhost:3000/support/orgs/test_org_id|Test Org>",
                    "type": "mrkdwn",
                },
                {
                    "text": ":clock3: <!date^1621449073^{date_short}, {time_secs}|2021-05-19T18:31:13.576657+00:00>",
                    "type": "mrkdwn",
                },
                {
                    "text": ":technologist: Audit admin test_user@example.com",
                    "type": "mrkdwn",
                },
            ],
            "type": "context",
        },
    ],
    "text": "test_user@example.com created an audit: Test Audit (Ballot Comparison)",
}

snapshots["test_slack_worker_message_format 10"] = {
    "blocks": [
        {
            "text": {
                "text": "*3 audit boards created for Test Jurisdiction*",
                "type": "mrkdwn",
            },
            "type": "section",
        },
        {
            "elements": [
                {
                    "text": ":flag-us: <http://localhost:3000/support/orgs/test_org_id|Test Org>",
                    "type": "mrkdwn",
                },
                {
                    "text": ":classical_building: <http://localhost:3000/support/orgs/test_jurisdiction_id|Test Jurisdiction> ",
                    "type": "mrkdwn",
                },
                {
                    "text": ":microscope: <http://localhost:3000/support/audits/test_election_id|Test Audit> (Hybrid)",
                    "type": "mrkdwn",
                },
                {
                    "text": ":clock3: <!date^1621449073^{date_short}, {time_secs}|2021-05-19T18:31:13.576657+00:00>",
                    "type": "mrkdwn",
                },
                {
                    "text": ":technologist: Jurisdiction admin test_user@example.com",
                    "type": "mrkdwn",
                },
            ],
            "type": "context",
        },
    ],
    "text": "3 audit boards created for Test Jurisdiction",
}

snapshots["test_slack_worker_message_format 11"] = {
    "blocks": [
        {
            "text": {
                "text": "*Results recorded for Test Jurisdiction*",
                "type": "mrkdwn",
            },
            "type": "section",
        },
        {
            "elements": [
                {
                    "text": ":flag-us: <http://localhost:3000/support/orgs/test_org_id|Test Org>",
                    "type": "mrkdwn",
                },
                {
                    "text": ":classical_building: <http://localhost:3000/support/orgs/test_jurisdiction_id|Test Jurisdiction> ",
                    "type": "mrkdwn",
                },
                {
                    "text": ":microscope: <http://localhost:3000/support/audits/test_election_id|Test Audit> (Hybrid)",
                    "type": "mrkdwn",
                },
                {
                    "text": ":clock3: <!date^1621449073^{date_short}, {time_secs}|2021-05-19T18:31:13.576657+00:00>",
                    "type": "mrkdwn",
                },
                {
                    "text": ":technologist: Jurisdiction admin test_user@example.com",
                    "type": "mrkdwn",
                },
            ],
            "type": "context",
        },
    ],
    "text": "Results recorded for Test Jurisdiction",
}

snapshots["test_slack_worker_message_format 12"] = {
    "blocks": [
        {
            "text": {
                "text": "*Audit Board #1 in Test Jurisdiction signed off*",
                "type": "mrkdwn",
            },
            "type": "section",
        },
        {
            "elements": [
                {
                    "text": ":flag-us: <http://localhost:3000/support/orgs/test_org_id|Test Org>",
                    "type": "mrkdwn",
                },
                {
                    "text": ":classical_building: <http://localhost:3000/support/orgs/test_jurisdiction_id|Test Jurisdiction> ",
                    "type": "mrkdwn",
                },
                {
                    "text": ":microscope: <http://localhost:3000/support/audits/test_election_id|Test Audit> (Hybrid)",
                    "type": "mrkdwn",
                },
                {
                    "text": ":clock3: <!date^1621449073^{date_short}, {time_secs}|2021-05-19T18:31:13.576657+00:00>",
                    "type": "mrkdwn",
                },
                {"text": ":technologist:  Audit Board #1", "type": "mrkdwn"},
            ],
            "type": "context",
        },
    ],
    "text": "Audit Board #1 in Test Jurisdiction signed off",
}

snapshots["test_slack_worker_message_format 2"] = {
    "blocks": [
        {
            "text": {
                "text": "*support_user@example.com deleted an audit: <http://localhost:3000/support/audits/test_election_id|Test Audit>* (Batch Comparison)",
                "type": "mrkdwn",
            },
            "type": "section",
        },
        {
            "elements": [
                {
                    "text": ":flag-us: <http://localhost:3000/support/orgs/test_org_id|Test Org>",
                    "type": "mrkdwn",
                },
                {
                    "text": ":clock3: <!date^1621449073^{date_short}, {time_secs}|2021-05-19T18:31:13.576657+00:00>",
                    "type": "mrkdwn",
                },
                {
                    "text": ":technologist: Support user support_user@example.com logged in as audit admin test_user@example.com",
                    "type": "mrkdwn",
                },
            ],
            "type": "context",
        },
    ],
    "text": "support_user@example.com deleted an audit: Test Audit (Batch Comparison)",
}

snapshots["test_slack_worker_message_format 3"] = {
    "blocks": [
        {
            "text": {
                "text": "*test_user@example.com started round 1*",
                "type": "mrkdwn",
            },
            "type": "section",
        },
        {
            "elements": [
                {
                    "text": ":flag-us: <http://localhost:3000/support/orgs/test_org_id|Test Org>",
                    "type": "mrkdwn",
                },
                {
                    "text": ":microscope: <http://localhost:3000/support/audits/test_election_id|Test Audit> (Ballot Comparison)",
                    "type": "mrkdwn",
                },
                {
                    "text": ":clock3: <!date^1621449073^{date_short}, {time_secs}|2021-05-19T18:31:13.576657+00:00>",
                    "type": "mrkdwn",
                },
                {
                    "text": ":technologist: Audit admin test_user@example.com",
                    "type": "mrkdwn",
                },
            ],
            "type": "context",
        },
    ],
    "text": "test_user@example.com started round 1",
}

snapshots["test_slack_worker_message_format 4"] = {
    "blocks": [
        {
            "text": {
                "text": "*Round 1 ended, another round is needed*",
                "type": "mrkdwn",
            },
            "type": "section",
        },
        {
            "elements": [
                {
                    "text": ":flag-us: <http://localhost:3000/support/orgs/test_org_id|Test Org>",
                    "type": "mrkdwn",
                },
                {
                    "text": ":microscope: <http://localhost:3000/support/audits/test_election_id|Test Audit> (Hybrid)",
                    "type": "mrkdwn",
                },
                {
                    "text": ":clock3: <!date^1621449073^{date_short}, {time_secs}|2021-05-19T18:31:13.576657+00:00>",
                    "type": "mrkdwn",
                },
            ],
            "type": "context",
        },
    ],
    "text": "Round 1 ended, another round is needed",
}

snapshots["test_slack_worker_message_format 5"] = {
    "blocks": [
        {
            "text": {"text": "*Round 2 ended, audit complete*", "type": "mrkdwn"},
            "type": "section",
        },
        {
            "elements": [
                {
                    "text": ":flag-us: <http://localhost:3000/support/orgs/test_org_id|Test Org>",
                    "type": "mrkdwn",
                },
                {
                    "text": ":microscope: <http://localhost:3000/support/audits/test_election_id|Test Audit> (Hybrid)",
                    "type": "mrkdwn",
                },
                {
                    "text": ":clock3: <!date^1621449073^{date_short}, {time_secs}|2021-05-19T18:31:13.576657+00:00>",
                    "type": "mrkdwn",
                },
            ],
            "type": "context",
        },
    ],
    "text": "Round 2 ended, audit complete",
}

snapshots["test_slack_worker_message_format 6"] = {
    "blocks": [
        {
            "text": {
                "text": "*test_user@example.com calculated sample sizes*",
                "type": "mrkdwn",
            },
            "type": "section",
        },
        {
            "elements": [
                {
                    "text": ":flag-us: <http://localhost:3000/support/orgs/test_org_id|Test Org>",
                    "type": "mrkdwn",
                },
                {
                    "text": ":microscope: <http://localhost:3000/support/audits/test_election_id|Test Audit> (Hybrid)",
                    "type": "mrkdwn",
                },
                {
                    "text": ":clock3: <!date^1621449073^{date_short}, {time_secs}|2021-05-19T18:31:13.576657+00:00>",
                    "type": "mrkdwn",
                },
                {
                    "text": ":technologist: Audit admin test_user@example.com",
                    "type": "mrkdwn",
                },
            ],
            "type": "context",
        },
    ],
    "text": "test_user@example.com calculated sample sizes",
}

snapshots["test_slack_worker_message_format 7"] = {
    "blocks": [
        {
            "text": {
                "text": "*Ballot manifest upload succeeded for Test Jurisdiction*",
                "type": "mrkdwn",
            },
            "type": "section",
        },
        {
            "elements": [
                {
                    "text": ":flag-us: <http://localhost:3000/support/orgs/test_org_id|Test Org>",
                    "type": "mrkdwn",
                },
                {
                    "text": ":classical_building: <http://localhost:3000/support/orgs/test_jurisdiction_id|Test Jurisdiction> ",
                    "type": "mrkdwn",
                },
                {
                    "text": ":microscope: <http://localhost:3000/support/audits/test_election_id|Test Audit> (Hybrid)",
                    "type": "mrkdwn",
                },
                {
                    "text": ":clock3: <!date^1621449073^{date_short}, {time_secs}|2021-05-19T18:31:13.576657+00:00>",
                    "type": "mrkdwn",
                },
            ],
            "type": "context",
        },
    ],
    "text": "Ballot manifest upload succeeded for Test Jurisdiction",
}

snapshots["test_slack_worker_message_format 8"] = {
    "blocks": [
        {
            "text": {
                "text": "*CVR upload failed for Test Jurisdiction*",
                "type": "mrkdwn",
            },
            "type": "section",
        },
        {
            "elements": [{"text": ":x: Something went wrong", "type": "mrkdwn"}],
            "type": "context",
        },
        {
            "elements": [
                {
                    "text": ":flag-us: <http://localhost:3000/support/orgs/test_org_id|Test Org>",
                    "type": "mrkdwn",
                },
                {
                    "text": ":classical_building: <http://localhost:3000/support/orgs/test_jurisdiction_id|Test Jurisdiction> ",
                    "type": "mrkdwn",
                },
                {
                    "text": ":microscope: <http://localhost:3000/support/audits/test_election_id|Test Audit> (Hybrid)",
                    "type": "mrkdwn",
                },
                {
                    "text": ":clock3: <!date^1621449073^{date_short}, {time_secs}|2021-05-19T18:31:13.576657+00:00>",
                    "type": "mrkdwn",
                },
            ],
            "type": "context",
        },
    ],
    "text": "CVR upload failed for Test Jurisdiction",
}

snapshots["test_slack_worker_message_format 9"] = {
    "blocks": [
        {
            "text": {
                "text": "*Batch tallies upload succeeded for Test Jurisdiction*",
                "type": "mrkdwn",
            },
            "type": "section",
        },
        {
            "elements": [
                {
                    "text": ":flag-us: <http://localhost:3000/support/orgs/test_org_id|Test Org>",
                    "type": "mrkdwn",
                },
                {
                    "text": ":classical_building: <http://localhost:3000/support/orgs/test_jurisdiction_id|Test Jurisdiction> ",
                    "type": "mrkdwn",
                },
                {
                    "text": ":microscope: <http://localhost:3000/support/audits/test_election_id|Test Audit> (Hybrid)",
                    "type": "mrkdwn",
                },
                {
                    "text": ":clock3: <!date^1621449073^{date_short}, {time_secs}|2021-05-19T18:31:13.576657+00:00>",
                    "type": "mrkdwn",
                },
            ],
            "type": "context",
        },
    ],
    "text": "Batch tallies upload succeeded for Test Jurisdiction",
}
