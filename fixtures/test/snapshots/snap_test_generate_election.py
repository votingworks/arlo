# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots["test_simple_election 1"] = {
    "Jurisdiction 1": {
        "Contest 1": {
            "invalid_votes": 1,
            "tally": {"Candidate 1": 9, "Candidate 2": 1, "Candidate 3": 0},
        }
    },
    "Jurisdiction 2": {
        "Contest 1": {
            "invalid_votes": 1,
            "tally": {"Candidate 1": 6, "Candidate 2": 2, "Candidate 3": 0},
        }
    },
    "Jurisdiction 3": {},
}

snapshots["test_simple_election 2"] = [
    {
        "ballot_number": 1,
        "batch": {"name": "Batch 1", "tabulator": "Tabulator A"},
        "votes": {"Contest 1": {"Candidate 1": 1, "Candidate 2": 0, "Candidate 3": 0}},
    },
    {
        "ballot_number": 2,
        "batch": {"name": "Batch 1", "tabulator": "Tabulator A"},
        "votes": {"Contest 1": {"Candidate 1": 1, "Candidate 2": 0, "Candidate 3": 0}},
    },
    {
        "ballot_number": 1,
        "batch": {"name": "Batch 2", "tabulator": "Tabulator B"},
        "votes": {"Contest 1": {"Candidate 1": 1, "Candidate 2": 0, "Candidate 3": 0}},
    },
    {
        "ballot_number": 2,
        "batch": {"name": "Batch 2", "tabulator": "Tabulator B"},
        "votes": {"Contest 1": {"Candidate 1": 1, "Candidate 2": 0, "Candidate 3": 0}},
    },
    {
        "ballot_number": 1,
        "batch": {"name": "Batch 3", "tabulator": "Tabulator C"},
        "votes": {"Contest 1": {"Candidate 1": 0, "Candidate 2": 1, "Candidate 3": 0}},
    },
    {
        "ballot_number": 1,
        "batch": {"name": "Batch 4", "tabulator": "Tabulator A"},
        "votes": {"Contest 1": {"Candidate 1": 0, "Candidate 2": 0, "Candidate 3": 0}},
    },
    {
        "ballot_number": 2,
        "batch": {"name": "Batch 4", "tabulator": "Tabulator A"},
        "votes": {"Contest 1": {"Candidate 1": 1, "Candidate 2": 0, "Candidate 3": 0}},
    },
    {
        "ballot_number": 1,
        "batch": {"name": "Batch 5", "tabulator": "Tabulator B"},
        "votes": {"Contest 1": {"Candidate 1": 1, "Candidate 2": 0, "Candidate 3": 0}},
    },
    {
        "ballot_number": 2,
        "batch": {"name": "Batch 5", "tabulator": "Tabulator B"},
        "votes": {"Contest 1": {"Candidate 1": 1, "Candidate 2": 0, "Candidate 3": 0}},
    },
    {
        "ballot_number": 1,
        "batch": {"name": "Batch 9", "tabulator": "Tabulator C"},
        "votes": {"Contest 1": {"Candidate 1": 1, "Candidate 2": 0, "Candidate 3": 0}},
    },
    {
        "ballot_number": 2,
        "batch": {"name": "Batch 9", "tabulator": "Tabulator C"},
        "votes": {"Contest 1": {"Candidate 1": 1, "Candidate 2": 0, "Candidate 3": 0}},
    },
]

snapshots["test_simple_election 3"] = [
    ({"name": "Batch 1", "tabulator": "Tabulator A"}, 2),
    ({"name": "Batch 2", "tabulator": "Tabulator B"}, 2),
    ({"name": "Batch 3", "tabulator": "Tabulator C"}, 1),
    ({"name": "Batch 4", "tabulator": "Tabulator A"}, 2),
    ({"name": "Batch 5", "tabulator": "Tabulator B"}, 2),
    ({"name": "Batch 9", "tabulator": "Tabulator C"}, 2),
]

snapshots["test_simple_election 4"] = [
    ("Batch 1", {"Candidate 1": 2, "Candidate 2": 0, "Candidate 3": 0}),
    ("Batch 2", {"Candidate 1": 2, "Candidate 2": 0, "Candidate 3": 0}),
    ("Batch 3", {"Candidate 1": 0, "Candidate 2": 1, "Candidate 3": 0}),
    ("Batch 4", {"Candidate 1": 1, "Candidate 2": 0, "Candidate 3": 0}),
    ("Batch 5", {"Candidate 1": 2, "Candidate 2": 0, "Candidate 3": 0}),
    ("Batch 9", {"Candidate 1": 2, "Candidate 2": 0, "Candidate 3": 0}),
]

snapshots["test_simple_election 5"] = [
    {
        "ballot_number": 1,
        "batch": {"name": "Batch 1", "tabulator": "Tabulator A"},
        "votes": {"Contest 1": {"Candidate 1": 1, "Candidate 2": 0, "Candidate 3": 0}},
    },
    {
        "ballot_number": 2,
        "batch": {"name": "Batch 1", "tabulator": "Tabulator A"},
        "votes": {"Contest 1": {"Candidate 1": 0, "Candidate 2": 0, "Candidate 3": 0}},
    },
    {
        "ballot_number": 1,
        "batch": {"name": "Batch 3", "tabulator": "Tabulator C"},
        "votes": {"Contest 1": {"Candidate 1": 1, "Candidate 2": 0, "Candidate 3": 0}},
    },
    {
        "ballot_number": 2,
        "batch": {"name": "Batch 3", "tabulator": "Tabulator C"},
        "votes": {"Contest 1": {"Candidate 1": 0, "Candidate 2": 1, "Candidate 3": 0}},
    },
    {
        "ballot_number": 1,
        "batch": {"name": "Batch 5", "tabulator": "Tabulator B"},
        "votes": {"Contest 1": {"Candidate 1": 0, "Candidate 2": 1, "Candidate 3": 0}},
    },
    {
        "ballot_number": 1,
        "batch": {"name": "Batch 7", "tabulator": "Tabulator A"},
        "votes": {"Contest 1": {"Candidate 1": 1, "Candidate 2": 0, "Candidate 3": 0}},
    },
    {
        "ballot_number": 2,
        "batch": {"name": "Batch 7", "tabulator": "Tabulator A"},
        "votes": {"Contest 1": {"Candidate 1": 1, "Candidate 2": 0, "Candidate 3": 0}},
    },
    {
        "ballot_number": 1,
        "batch": {"name": "Batch 8", "tabulator": "Tabulator B"},
        "votes": {"Contest 1": {"Candidate 1": 1, "Candidate 2": 0, "Candidate 3": 0}},
    },
    {
        "ballot_number": 1,
        "batch": {"name": "Batch 10", "tabulator": "Tabulator A"},
        "votes": {"Contest 1": {"Candidate 1": 1, "Candidate 2": 0, "Candidate 3": 0}},
    },
]

snapshots["test_simple_election 6"] = [
    ({"name": "Batch 1", "tabulator": "Tabulator A"}, 2),
    ({"name": "Batch 3", "tabulator": "Tabulator C"}, 2),
    ({"name": "Batch 5", "tabulator": "Tabulator B"}, 1),
    ({"name": "Batch 7", "tabulator": "Tabulator A"}, 2),
    ({"name": "Batch 8", "tabulator": "Tabulator B"}, 1),
    ({"name": "Batch 10", "tabulator": "Tabulator A"}, 1),
]

snapshots["test_simple_election 7"] = [
    ("Batch 1", {"Candidate 1": 1, "Candidate 2": 0, "Candidate 3": 0}),
    ("Batch 3", {"Candidate 1": 1, "Candidate 2": 1, "Candidate 3": 0}),
    ("Batch 5", {"Candidate 1": 0, "Candidate 2": 1, "Candidate 3": 0}),
    ("Batch 7", {"Candidate 1": 2, "Candidate 2": 0, "Candidate 3": 0}),
    ("Batch 8", {"Candidate 1": 1, "Candidate 2": 0, "Candidate 3": 0}),
    ("Batch 10", {"Candidate 1": 1, "Candidate 2": 0, "Candidate 3": 0}),
]

snapshots["test_simple_election 8"] = []

snapshots["test_simple_election 9"] = []
