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
"2. Ensure that ballot numbers match. If there is a large discrepancy, contact the SOS."\r
\r
Ballot Group,CVR Ballot Count,Checked?\r
Election Day,13,\r
Mail,2,\r
\r
Section 2: Check Batches\r
1. Locate each batch in storage.\r
"2. Confirm the CVR Ballot Count is correct. If there is a large discrepancy, contact the SOS."\r
3. Make sure there are no batches missing from this worksheet.\r
\r
Batch,CVR Ballot Count,Checked?\r
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
