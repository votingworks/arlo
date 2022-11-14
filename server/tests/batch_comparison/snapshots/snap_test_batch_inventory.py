# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots[
    "test_batch_inventory_happy_path 1"
] = """Batch Inventory Worksheet\r
\r
Section 1: Check Ballot Groups\r
1. Compare the CVR Ballot Count for each ballot group to your voter check-in data.\r
2. Ensure that the numbers reconcile. If there is a large discrepancy contact your SOS liaison.\r
\r
Ballot Group,CVR Ballot Count,Checked? (Type Yes/No)\r
Election Day,13,\r
Mail,2,\r
\r
Section 2: Check Batches\r
1. Locate each batch in storage.\r
2. Confirm the CVR Ballot Count is correct using associated documentation. Do NOT count the ballots. If there is a large discrepancy contact your SOS liaison.\r
3. Make sure there are no batches missing from this worksheet.\r
\r
Batch,CVR Ballot Count,Checked? (Type Yes/No)\r
Tabulator 1 - BATCH1,3,\r
Tabulator 1 - BATCH2,3,\r
Tabulator 2 - BATCH1,3,\r
Tabulator 2 - BATCH2,6,\r
"""

snapshots[
    "test_batch_inventory_happy_path 2"
] = """Container,Batch Name,Number of Ballots\r
Election Day,Tabulator 1 - BATCH1,3\r
Election Day,Tabulator 1 - BATCH2,3\r
Mail,Tabulator 2 - BATCH1,3\r
Election Day,Tabulator 2 - BATCH2,6\r
"""

snapshots[
    "test_batch_inventory_happy_path 3"
] = """Batch Name,Choice 1-1,Choice 1-2\r
Tabulator 1 - BATCH1,1,2\r
Tabulator 1 - BATCH2,2,1\r
Tabulator 2 - BATCH1,2,1\r
Tabulator 2 - BATCH2,2,0\r
"""
