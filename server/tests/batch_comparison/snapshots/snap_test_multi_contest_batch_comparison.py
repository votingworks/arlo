# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots[
    "test_multi_contest_batch_comparison_end_to_end 1"
] = """######## SAMPLED BATCHES ########\r
Jurisdiction Name,Batch Name,Ballots in Batch,Ticket Numbers: Contest 1,Ticket Numbers: Contest 2,Audited?,Audit Results: Contest 1,Reported Results: Contest 1,Change in Results: Contest 1,Change in Margin: Contest 1,Audit Results: Contest 2,Reported Results: Contest 2,Change in Results: Contest 2,Change in Margin: Contest 2,Last Edited By\r
J1,Batch 1,100,,"Round 1: 0.720194360819624066, 0.777128466487428756",Yes,Candidate 1: 50; Candidate 2: 0,Candidate 1: 50; Candidate 2: 0,,,Candidate 3: 50; Candidate 4: 0,Candidate 3: 50; Candidate 4: 0,,,jurisdiction.admin-UUID@example.com\r
J1,Batch 2,100,"Round 1: 0.474971525750860236, 0.555845039101209884",,Yes,Candidate 1: 50; Candidate 2: 0,Candidate 1: 50; Candidate 2: 0,,,Candidate 3: 50; Candidate 4: 0,Candidate 3: 50; Candidate 4: 0,,,jurisdiction.admin-UUID@example.com\r
J1,Batch 3,100,,Round 1: 0.753710009967479876,Yes,Candidate 1: 50; Candidate 2: 0,Candidate 1: 50; Candidate 2: 0,,,Candidate 3: 50; Candidate 4: 0,Candidate 3: 50; Candidate 4: 0,,,jurisdiction.admin-UUID@example.com\r
J1,Batch 5,100,"Round 1: 0.384177151866437890, 0.470460412141498108","Round 1: 0.384177151866437890, 0.470460412141498108",Yes,Candidate 1: 50; Candidate 2: 0,Candidate 1: 50; Candidate 2: 0,,,Candidate 3: 50; Candidate 4: 0,Candidate 3: 50; Candidate 4: 0,,,jurisdiction.admin-UUID@example.com\r
J1,Batch 6,100,"Round 1: 0.899217854763070950, 0.9233199163410086672",,Yes,Candidate 1: 49; Candidate 2: 1,Candidate 1: 50; Candidate 2: 0,Candidate 1: +1; Candidate 2: -1,2,Candidate 3: 50; Candidate 4: 0,Candidate 3: 50; Candidate 4: 0,,,jurisdiction.admin-UUID@example.com\r
J1,Batch 7,100,Round 1: 0.817464900879746084,"Round 1: 0.817464900879746084, 0.864505270651837742",Yes,Candidate 1: 50; Candidate 2: 0,Candidate 1: 50; Candidate 2: 0,,,Candidate 3: 49; Candidate 4: 1,Candidate 3: 50; Candidate 4: 0,Candidate 3: +1; Candidate 4: -1,2,jurisdiction.admin-UUID@example.com\r
J1,Batch 9,100,,Round 1: 0.734926612730309894,Yes,Candidate 1: 52; Candidate 2: 0,Candidate 1: 50; Candidate 2: 0,Candidate 1: -2,-2,Candidate 3: 26; Candidate 4: 24,Candidate 3: 25; Candidate 4: 25,Candidate 3: -1; Candidate 4: +1,-2,jurisdiction.admin-UUID@example.com\r
Totals,,700,,,,Candidate 1: 351; Candidate 2: 1,Candidate 1: 350; Candidate 2: 0,,,Candidate 3: 325; Candidate 4: 25,Candidate 3: 325; Candidate 4: 25,,\r
"""

snapshots[
    "test_multi_contest_batch_comparison_end_to_end 2"
] = """######## ELECTION INFO ########\r
Organization,Election Name,State\r
Test Org test_multi_contest_batch_comparison_end_to_end,Test Election,CA\r
\r
######## CONTESTS ########\r
Contest Name,Targeted?,Number of Winners,Votes Allowed,Total Ballots Cast,Tabulated Votes\r
Contest 1,Targeted,1,1,1500,Candidate 1: 750; Candidate 2: 250\r
Contest 2,Targeted,1,2,1000,Candidate 3: 450; Candidate 4: 50\r
\r
######## AUDIT SETTINGS ########\r
Audit Name,Audit Type,Audit Math Type,Risk Limit,Random Seed,Online Data Entry?\r
Test Audit test_multi_contest_batch_comparison_end_to_end,BATCH_COMPARISON,MACRO,10%,1234567890,No\r
\r
######## ROUNDS ########\r
Round Number,Contest Name,Targeted?,Sample Size,Risk Limit Met?,P-Value,Start Time,End Time,Audited Votes,Batches Sampled,Ballots Sampled,Reported Votes\r
1,Contest 1,Targeted,10,No,,DATETIME,,Candidate 1: 0; Candidate 2: 0,9,900,Candidate 1: 500; Candidate 2: 50\r
1,Contest 2,Targeted,8,No,,DATETIME,,Candidate 3: 0; Candidate 4: 0,9,900,Candidate 3: 325; Candidate 4: 25\r
\r
######## SAMPLED BATCHES ########\r
Jurisdiction Name,Batch Name,Ballots in Batch,Ticket Numbers: Contest 1,Ticket Numbers: Contest 2,Audited?,Audit Results: Contest 1,Reported Results: Contest 1,Change in Results: Contest 1,Change in Margin: Contest 1,Audit Results: Contest 2,Reported Results: Contest 2,Change in Results: Contest 2,Change in Margin: Contest 2,Last Edited By\r
J1,Batch 1,100,,"Round 1: 0.720194360819624066, 0.777128466487428756",Yes,Candidate 1: 50; Candidate 2: 0,Candidate 1: 50; Candidate 2: 0,,,Candidate 3: 50; Candidate 4: 0,Candidate 3: 50; Candidate 4: 0,,,jurisdiction.admin-UUID@example.com\r
J1,Batch 2,100,"Round 1: 0.474971525750860236, 0.555845039101209884",,Yes,Candidate 1: 50; Candidate 2: 0,Candidate 1: 50; Candidate 2: 0,,,Candidate 3: 50; Candidate 4: 0,Candidate 3: 50; Candidate 4: 0,,,jurisdiction.admin-UUID@example.com\r
J1,Batch 3,100,,Round 1: 0.753710009967479876,Yes,Candidate 1: 50; Candidate 2: 0,Candidate 1: 50; Candidate 2: 0,,,Candidate 3: 50; Candidate 4: 0,Candidate 3: 50; Candidate 4: 0,,,jurisdiction.admin-UUID@example.com\r
J1,Batch 5,100,"Round 1: 0.384177151866437890, 0.470460412141498108","Round 1: 0.384177151866437890, 0.470460412141498108",Yes,Candidate 1: 50; Candidate 2: 0,Candidate 1: 50; Candidate 2: 0,,,Candidate 3: 50; Candidate 4: 0,Candidate 3: 50; Candidate 4: 0,,,jurisdiction.admin-UUID@example.com\r
J1,Batch 6,100,"Round 1: 0.899217854763070950, 0.9233199163410086672",,Yes,Candidate 1: 49; Candidate 2: 1,Candidate 1: 50; Candidate 2: 0,Candidate 1: +1; Candidate 2: -1,2,Candidate 3: 50; Candidate 4: 0,Candidate 3: 50; Candidate 4: 0,,,jurisdiction.admin-UUID@example.com\r
J1,Batch 7,100,Round 1: 0.817464900879746084,"Round 1: 0.817464900879746084, 0.864505270651837742",Yes,Candidate 1: 50; Candidate 2: 0,Candidate 1: 50; Candidate 2: 0,,,Candidate 3: 49; Candidate 4: 1,Candidate 3: 50; Candidate 4: 0,Candidate 3: +1; Candidate 4: -1,2,jurisdiction.admin-UUID@example.com\r
J1,Batch 9,100,,Round 1: 0.734926612730309894,Yes,Candidate 1: 52; Candidate 2: 0,Candidate 1: 50; Candidate 2: 0,Candidate 1: -2,-2,Candidate 3: 26; Candidate 4: 24,Candidate 3: 25; Candidate 4: 25,Candidate 3: -1; Candidate 4: +1,-2,jurisdiction.admin-UUID@example.com\r
J2,Batch 1,100,"Round 1: 0.562697240648997100, 0.9008218268717084008",,No,,,,,,,,,\r
J3,Batch 1,100,Round 1: 0.544165663445275136,,No,,,,,,,,,\r
Totals,,900,,,,Candidate 1: 351; Candidate 2: 1,Candidate 1: 350; Candidate 2: 0,,,Candidate 3: 325; Candidate 4: 25,Candidate 3: 325; Candidate 4: 25,,\r
"""

snapshots[
    "test_multi_contest_batch_comparison_end_to_end 3"
] = """######## ELECTION INFO ########\r
Organization,Election Name,State\r
Test Org test_multi_contest_batch_comparison_end_to_end,Test Election,CA\r
\r
######## CONTESTS ########\r
Contest Name,Targeted?,Number of Winners,Votes Allowed,Total Ballots Cast,Tabulated Votes\r
Contest 1,Targeted,1,1,1500,Candidate 1: 750; Candidate 2: 250\r
Contest 2,Targeted,1,2,1000,Candidate 3: 450; Candidate 4: 50\r
\r
######## AUDIT SETTINGS ########\r
Audit Name,Audit Type,Audit Math Type,Risk Limit,Random Seed,Online Data Entry?\r
Test Audit test_multi_contest_batch_comparison_end_to_end,BATCH_COMPARISON,MACRO,10%,1234567890,No\r
\r
######## ROUNDS ########\r
Round Number,Contest Name,Targeted?,Sample Size,Risk Limit Met?,P-Value,Start Time,End Time,Audited Votes,Batches Sampled,Ballots Sampled,Reported Votes\r
1,Contest 1,Targeted,10,Yes,0.0771277137,DATETIME,DATETIME,Candidate 1: 500; Candidate 2: 52,9,900,Candidate 1: 500; Candidate 2: 50\r
1,Contest 2,Targeted,8,Yes,0.096146459,DATETIME,DATETIME,Candidate 3: 325; Candidate 4: 25,9,900,Candidate 3: 325; Candidate 4: 25\r
\r
######## SAMPLED BATCHES ########\r
Jurisdiction Name,Batch Name,Ballots in Batch,Ticket Numbers: Contest 1,Ticket Numbers: Contest 2,Audited?,Audit Results: Contest 1,Reported Results: Contest 1,Change in Results: Contest 1,Change in Margin: Contest 1,Audit Results: Contest 2,Reported Results: Contest 2,Change in Results: Contest 2,Change in Margin: Contest 2,Last Edited By\r
J1,Batch 1,100,,"Round 1: 0.720194360819624066, 0.777128466487428756",Yes,Candidate 1: 50; Candidate 2: 0,Candidate 1: 50; Candidate 2: 0,,,Candidate 3: 50; Candidate 4: 0,Candidate 3: 50; Candidate 4: 0,,,jurisdiction.admin-UUID@example.com\r
J1,Batch 2,100,"Round 1: 0.474971525750860236, 0.555845039101209884",,Yes,Candidate 1: 50; Candidate 2: 0,Candidate 1: 50; Candidate 2: 0,,,Candidate 3: 50; Candidate 4: 0,Candidate 3: 50; Candidate 4: 0,,,jurisdiction.admin-UUID@example.com\r
J1,Batch 3,100,,Round 1: 0.753710009967479876,Yes,Candidate 1: 50; Candidate 2: 0,Candidate 1: 50; Candidate 2: 0,,,Candidate 3: 50; Candidate 4: 0,Candidate 3: 50; Candidate 4: 0,,,jurisdiction.admin-UUID@example.com\r
J1,Batch 5,100,"Round 1: 0.384177151866437890, 0.470460412141498108","Round 1: 0.384177151866437890, 0.470460412141498108",Yes,Candidate 1: 50; Candidate 2: 0,Candidate 1: 50; Candidate 2: 0,,,Candidate 3: 50; Candidate 4: 0,Candidate 3: 50; Candidate 4: 0,,,jurisdiction.admin-UUID@example.com\r
J1,Batch 6,100,"Round 1: 0.899217854763070950, 0.9233199163410086672",,Yes,Candidate 1: 49; Candidate 2: 1,Candidate 1: 50; Candidate 2: 0,Candidate 1: +1; Candidate 2: -1,2,Candidate 3: 50; Candidate 4: 0,Candidate 3: 50; Candidate 4: 0,,,jurisdiction.admin-UUID@example.com\r
J1,Batch 7,100,Round 1: 0.817464900879746084,"Round 1: 0.817464900879746084, 0.864505270651837742",Yes,Candidate 1: 50; Candidate 2: 0,Candidate 1: 50; Candidate 2: 0,,,Candidate 3: 49; Candidate 4: 1,Candidate 3: 50; Candidate 4: 0,Candidate 3: +1; Candidate 4: -1,2,jurisdiction.admin-UUID@example.com\r
J1,Batch 9,100,,Round 1: 0.734926612730309894,Yes,Candidate 1: 52; Candidate 2: 0,Candidate 1: 50; Candidate 2: 0,Candidate 1: -2,-2,Candidate 3: 26; Candidate 4: 24,Candidate 3: 25; Candidate 4: 25,Candidate 3: -1; Candidate 4: +1,-2,jurisdiction.admin-UUID@example.com\r
J2,Batch 1,100,"Round 1: 0.562697240648997100, 0.9008218268717084008",,Yes,Candidate 1: 75; Candidate 2: 25,Candidate 1: 75; Candidate 2: 25,,,,,,,jurisdiction.admin-UUID@example.com\r
J3,Batch 1,100,Round 1: 0.544165663445275136,,Yes,Candidate 1: 74; Candidate 2: 26,Candidate 1: 75; Candidate 2: 25,Candidate 1: +1; Candidate 2: -1,2,,,,,jurisdiction.admin-UUID@example.com\r
Totals,,900,,,,Candidate 1: 500; Candidate 2: 52,Candidate 1: 500; Candidate 2: 50,,,Candidate 3: 325; Candidate 4: 25,Candidate 3: 325; Candidate 4: 25,,\r
"""

snapshots[
    "test_multi_contest_batch_comparison_round_2 1"
] = """######## ELECTION INFO ########\r
Organization,Election Name,State\r
Test Org test_multi_contest_batch_comparison_round_2,Test Election,CA\r
\r
######## CONTESTS ########\r
Contest Name,Targeted?,Number of Winners,Votes Allowed,Total Ballots Cast,Tabulated Votes\r
Contest 1,Targeted,1,1,1500,Candidate 1: 750; Candidate 2: 250\r
Contest 2,Targeted,1,2,1000,Candidate 3: 450; Candidate 4: 50\r
\r
######## AUDIT SETTINGS ########\r
Audit Name,Audit Type,Audit Math Type,Risk Limit,Random Seed,Online Data Entry?\r
Test Audit test_multi_contest_batch_comparison_round_2,BATCH_COMPARISON,MACRO,10%,1234567890,No\r
\r
######## ROUNDS ########\r
Round Number,Contest Name,Targeted?,Sample Size,Risk Limit Met?,P-Value,Start Time,End Time,Audited Votes,Batches Sampled,Ballots Sampled,Reported Votes\r
1,Contest 1,Targeted,10,No,0.1689405441,DATETIME,DATETIME,Candidate 1: 450; Candidate 2: 100,9,900,Candidate 1: 500; Candidate 2: 50\r
1,Contest 2,Targeted,8,Yes,0.0948645062,DATETIME,DATETIME,Candidate 3: 325; Candidate 4: 25,9,900,Candidate 3: 325; Candidate 4: 25\r
\r
######## SAMPLED BATCHES ########\r
Jurisdiction Name,Batch Name,Ballots in Batch,Ticket Numbers: Contest 1,Ticket Numbers: Contest 2,Audited?,Audit Results: Contest 1,Reported Results: Contest 1,Change in Results: Contest 1,Change in Margin: Contest 1,Audit Results: Contest 2,Reported Results: Contest 2,Change in Results: Contest 2,Change in Margin: Contest 2,Last Edited By\r
J1,Batch 1,100,,"Round 1: 0.720194360819624066, 0.777128466487428756",Yes,Candidate 1: 50; Candidate 2: 0,Candidate 1: 50; Candidate 2: 0,,,Candidate 3: 50; Candidate 4: 0,Candidate 3: 50; Candidate 4: 0,,,jurisdiction.admin-UUID@example.com\r
J1,Batch 2,100,"Round 1: 0.474971525750860236, 0.555845039101209884",,Yes,Candidate 1: 50; Candidate 2: 0,Candidate 1: 50; Candidate 2: 0,,,Candidate 3: 50; Candidate 4: 0,Candidate 3: 50; Candidate 4: 0,,,jurisdiction.admin-UUID@example.com\r
J1,Batch 3,100,,Round 1: 0.753710009967479876,Yes,Candidate 1: 50; Candidate 2: 0,Candidate 1: 50; Candidate 2: 0,,,Candidate 3: 50; Candidate 4: 0,Candidate 3: 50; Candidate 4: 0,,,jurisdiction.admin-UUID@example.com\r
J1,Batch 5,100,"Round 1: 0.384177151866437890, 0.470460412141498108","Round 1: 0.384177151866437890, 0.470460412141498108",Yes,Candidate 1: 50; Candidate 2: 0,Candidate 1: 50; Candidate 2: 0,,,Candidate 3: 50; Candidate 4: 0,Candidate 3: 50; Candidate 4: 0,,,jurisdiction.admin-UUID@example.com\r
J1,Batch 6,100,"Round 1: 0.899217854763070950, 0.9233199163410086672",,Yes,Candidate 1: 50; Candidate 2: 0,Candidate 1: 50; Candidate 2: 0,,,Candidate 3: 50; Candidate 4: 0,Candidate 3: 50; Candidate 4: 0,,,jurisdiction.admin-UUID@example.com\r
J1,Batch 7,100,Round 1: 0.817464900879746084,"Round 1: 0.817464900879746084, 0.864505270651837742",Yes,Candidate 1: 0; Candidate 2: 50,Candidate 1: 50; Candidate 2: 0,Candidate 1: +50; Candidate 2: -50,100,Candidate 3: 50; Candidate 4: 0,Candidate 3: 50; Candidate 4: 0,,,jurisdiction.admin-UUID@example.com\r
J1,Batch 9,100,,Round 1: 0.734926612730309894,Yes,Candidate 1: 50; Candidate 2: 0,Candidate 1: 50; Candidate 2: 0,,,Candidate 3: 25; Candidate 4: 25,Candidate 3: 25; Candidate 4: 25,,,jurisdiction.admin-UUID@example.com\r
J2,Batch 1,100,"Round 1: 0.562697240648997100, 0.9008218268717084008",,Yes,Candidate 1: 75; Candidate 2: 25,Candidate 1: 75; Candidate 2: 25,,,,,,,jurisdiction.admin-UUID@example.com\r
J3,Batch 1,100,Round 1: 0.544165663445275136,,Yes,Candidate 1: 75; Candidate 2: 25,Candidate 1: 75; Candidate 2: 25,,,,,,,jurisdiction.admin-UUID@example.com\r
Totals,,900,,,,Candidate 1: 450; Candidate 2: 100,Candidate 1: 500; Candidate 2: 50,,,Candidate 3: 325; Candidate 4: 25,Candidate 3: 325; Candidate 4: 25,,\r
"""

snapshots[
    "test_multi_contest_batch_comparison_round_2 2"
] = """######## ELECTION INFO ########\r
Organization,Election Name,State\r
Test Org test_multi_contest_batch_comparison_round_2,Test Election,CA\r
\r
######## CONTESTS ########\r
Contest Name,Targeted?,Number of Winners,Votes Allowed,Total Ballots Cast,Tabulated Votes\r
Contest 1,Targeted,1,1,1500,Candidate 1: 750; Candidate 2: 250\r
Contest 2,Targeted,1,2,1000,Candidate 3: 450; Candidate 4: 50\r
\r
######## AUDIT SETTINGS ########\r
Audit Name,Audit Type,Audit Math Type,Risk Limit,Random Seed,Online Data Entry?\r
Test Audit test_multi_contest_batch_comparison_round_2,BATCH_COMPARISON,MACRO,10%,1234567890,No\r
\r
######## ROUNDS ########\r
Round Number,Contest Name,Targeted?,Sample Size,Risk Limit Met?,P-Value,Start Time,End Time,Audited Votes,Batches Sampled,Ballots Sampled,Reported Votes\r
1,Contest 1,Targeted,10,No,0.1689405441,DATETIME,DATETIME,Candidate 1: 450; Candidate 2: 100,9,900,Candidate 1: 500; Candidate 2: 50\r
1,Contest 2,Targeted,8,Yes,0.0948645062,DATETIME,DATETIME,Candidate 3: 325; Candidate 4: 25,9,900,Candidate 3: 325; Candidate 4: 25\r
2,Contest 1,Targeted,6,No,,DATETIME,,Candidate 1: 0; Candidate 2: 0,6,600,Candidate 1: 350; Candidate 2: 50\r
\r
######## SAMPLED BATCHES ########\r
Jurisdiction Name,Batch Name,Ballots in Batch,Ticket Numbers: Contest 1,Ticket Numbers: Contest 2,Audited?,Audit Results: Contest 1,Reported Results: Contest 1,Change in Results: Contest 1,Change in Margin: Contest 1,Audit Results: Contest 2,Reported Results: Contest 2,Change in Results: Contest 2,Change in Margin: Contest 2,Last Edited By\r
J1,Batch 1,100,Round 2: 0.720194360819624066,"Round 1: 0.720194360819624066, 0.777128466487428756",Yes,Candidate 1: 50; Candidate 2: 0,Candidate 1: 50; Candidate 2: 0,,,Candidate 3: 50; Candidate 4: 0,Candidate 3: 50; Candidate 4: 0,,,jurisdiction.admin-UUID@example.com\r
J1,Batch 2,100,"Round 1: 0.474971525750860236, 0.555845039101209884",,Yes,Candidate 1: 50; Candidate 2: 0,Candidate 1: 50; Candidate 2: 0,,,Candidate 3: 50; Candidate 4: 0,Candidate 3: 50; Candidate 4: 0,,,jurisdiction.admin-UUID@example.com\r
J1,Batch 3,100,Round 2: 0.753710009967479876,Round 1: 0.753710009967479876,Yes,Candidate 1: 50; Candidate 2: 0,Candidate 1: 50; Candidate 2: 0,,,Candidate 3: 50; Candidate 4: 0,Candidate 3: 50; Candidate 4: 0,,,jurisdiction.admin-UUID@example.com\r
J1,Batch 5,100,"Round 1: 0.384177151866437890, 0.470460412141498108","Round 1: 0.384177151866437890, 0.470460412141498108",Yes,Candidate 1: 50; Candidate 2: 0,Candidate 1: 50; Candidate 2: 0,,,Candidate 3: 50; Candidate 4: 0,Candidate 3: 50; Candidate 4: 0,,,jurisdiction.admin-UUID@example.com\r
J1,Batch 6,100,"Round 1: 0.899217854763070950, 0.9233199163410086672, Round 2: 0.9773691435537901980",,Yes,Candidate 1: 50; Candidate 2: 0,Candidate 1: 50; Candidate 2: 0,,,Candidate 3: 50; Candidate 4: 0,Candidate 3: 50; Candidate 4: 0,,,jurisdiction.admin-UUID@example.com\r
J1,Batch 7,100,Round 1: 0.817464900879746084,"Round 1: 0.817464900879746084, 0.864505270651837742",Yes,Candidate 1: 0; Candidate 2: 50,Candidate 1: 50; Candidate 2: 0,Candidate 1: +50; Candidate 2: -50,100,Candidate 3: 50; Candidate 4: 0,Candidate 3: 50; Candidate 4: 0,,,jurisdiction.admin-UUID@example.com\r
J1,Batch 9,100,,Round 1: 0.734926612730309894,Yes,Candidate 1: 50; Candidate 2: 0,Candidate 1: 50; Candidate 2: 0,,,Candidate 3: 25; Candidate 4: 25,Candidate 3: 25; Candidate 4: 25,,,jurisdiction.admin-UUID@example.com\r
J2,Batch 1,100,"Round 1: 0.562697240648997100, 0.9008218268717084008, Round 2: 0.9809620734120025512",,Yes,Candidate 1: 75; Candidate 2: 25,Candidate 1: 75; Candidate 2: 25,,,,,,,jurisdiction.admin-UUID@example.com\r
J3,Batch 1,100,"Round 1: 0.544165663445275136, Round 2: 0.651158228740912018",,Yes,Candidate 1: 75; Candidate 2: 25,Candidate 1: 75; Candidate 2: 25,,,,,,,jurisdiction.admin-UUID@example.com\r
J1,Batch 8,100,Round 2: 0.9723790677174592551,,No,,Candidate 1: 50; Candidate 2: 0,,,,Candidate 3: 50; Candidate 4: 0,,,\r
Totals,,1000,,,,Candidate 1: 450; Candidate 2: 100,Candidate 1: 550; Candidate 2: 50,,,Candidate 3: 325; Candidate 4: 25,Candidate 3: 375; Candidate 4: 25,,\r
"""

snapshots[
    "test_multi_contest_batch_comparison_round_2 3"
] = """######## ELECTION INFO ########\r
Organization,Election Name,State\r
Test Org test_multi_contest_batch_comparison_round_2,Test Election,CA\r
\r
######## CONTESTS ########\r
Contest Name,Targeted?,Number of Winners,Votes Allowed,Total Ballots Cast,Tabulated Votes\r
Contest 1,Targeted,1,1,1500,Candidate 1: 750; Candidate 2: 250\r
Contest 2,Targeted,1,2,1000,Candidate 3: 450; Candidate 4: 50\r
\r
######## AUDIT SETTINGS ########\r
Audit Name,Audit Type,Audit Math Type,Risk Limit,Random Seed,Online Data Entry?\r
Test Audit test_multi_contest_batch_comparison_round_2,BATCH_COMPARISON,MACRO,10%,1234567890,No\r
\r
######## ROUNDS ########\r
Round Number,Contest Name,Targeted?,Sample Size,Risk Limit Met?,P-Value,Start Time,End Time,Audited Votes,Batches Sampled,Ballots Sampled,Reported Votes\r
1,Contest 1,Targeted,10,No,0.1689405441,DATETIME,DATETIME,Candidate 1: 450; Candidate 2: 100,9,900,Candidate 1: 500; Candidate 2: 50\r
1,Contest 2,Targeted,8,Yes,0.0948645062,DATETIME,DATETIME,Candidate 3: 325; Candidate 4: 25,9,900,Candidate 3: 325; Candidate 4: 25\r
2,Contest 1,Targeted,6,Yes,0.0750846863,DATETIME,DATETIME,Candidate 1: 350; Candidate 2: 50,6,600,Candidate 1: 350; Candidate 2: 50\r
\r
######## SAMPLED BATCHES ########\r
Jurisdiction Name,Batch Name,Ballots in Batch,Ticket Numbers: Contest 1,Ticket Numbers: Contest 2,Audited?,Audit Results: Contest 1,Reported Results: Contest 1,Change in Results: Contest 1,Change in Margin: Contest 1,Audit Results: Contest 2,Reported Results: Contest 2,Change in Results: Contest 2,Change in Margin: Contest 2,Last Edited By\r
J1,Batch 1,100,Round 2: 0.720194360819624066,"Round 1: 0.720194360819624066, 0.777128466487428756",Yes,Candidate 1: 50; Candidate 2: 0,Candidate 1: 50; Candidate 2: 0,,,Candidate 3: 50; Candidate 4: 0,Candidate 3: 50; Candidate 4: 0,,,jurisdiction.admin-UUID@example.com\r
J1,Batch 2,100,"Round 1: 0.474971525750860236, 0.555845039101209884",,Yes,Candidate 1: 50; Candidate 2: 0,Candidate 1: 50; Candidate 2: 0,,,Candidate 3: 50; Candidate 4: 0,Candidate 3: 50; Candidate 4: 0,,,jurisdiction.admin-UUID@example.com\r
J1,Batch 3,100,Round 2: 0.753710009967479876,Round 1: 0.753710009967479876,Yes,Candidate 1: 50; Candidate 2: 0,Candidate 1: 50; Candidate 2: 0,,,Candidate 3: 50; Candidate 4: 0,Candidate 3: 50; Candidate 4: 0,,,jurisdiction.admin-UUID@example.com\r
J1,Batch 5,100,"Round 1: 0.384177151866437890, 0.470460412141498108","Round 1: 0.384177151866437890, 0.470460412141498108",Yes,Candidate 1: 50; Candidate 2: 0,Candidate 1: 50; Candidate 2: 0,,,Candidate 3: 50; Candidate 4: 0,Candidate 3: 50; Candidate 4: 0,,,jurisdiction.admin-UUID@example.com\r
J1,Batch 6,100,"Round 1: 0.899217854763070950, 0.9233199163410086672, Round 2: 0.9773691435537901980",,Yes,Candidate 1: 50; Candidate 2: 0,Candidate 1: 50; Candidate 2: 0,,,Candidate 3: 50; Candidate 4: 0,Candidate 3: 50; Candidate 4: 0,,,jurisdiction.admin-UUID@example.com\r
J1,Batch 7,100,Round 1: 0.817464900879746084,"Round 1: 0.817464900879746084, 0.864505270651837742",Yes,Candidate 1: 0; Candidate 2: 50,Candidate 1: 50; Candidate 2: 0,Candidate 1: +50; Candidate 2: -50,100,Candidate 3: 50; Candidate 4: 0,Candidate 3: 50; Candidate 4: 0,,,jurisdiction.admin-UUID@example.com\r
J1,Batch 9,100,,Round 1: 0.734926612730309894,Yes,Candidate 1: 50; Candidate 2: 0,Candidate 1: 50; Candidate 2: 0,,,Candidate 3: 25; Candidate 4: 25,Candidate 3: 25; Candidate 4: 25,,,jurisdiction.admin-UUID@example.com\r
J2,Batch 1,100,"Round 1: 0.562697240648997100, 0.9008218268717084008, Round 2: 0.9809620734120025512",,Yes,Candidate 1: 75; Candidate 2: 25,Candidate 1: 75; Candidate 2: 25,,,,,,,jurisdiction.admin-UUID@example.com\r
J3,Batch 1,100,"Round 1: 0.544165663445275136, Round 2: 0.651158228740912018",,Yes,Candidate 1: 75; Candidate 2: 25,Candidate 1: 75; Candidate 2: 25,,,,,,,jurisdiction.admin-UUID@example.com\r
J1,Batch 8,100,Round 2: 0.9723790677174592551,,Yes,Candidate 1: 50; Candidate 2: 0,Candidate 1: 50; Candidate 2: 0,,,Candidate 3: 50; Candidate 4: 0,Candidate 3: 50; Candidate 4: 0,,,jurisdiction.admin-UUID@example.com\r
Totals,,1000,,,,Candidate 1: 500; Candidate 2: 100,Candidate 1: 550; Candidate 2: 50,,,Candidate 3: 375; Candidate 4: 25,Candidate 3: 375; Candidate 4: 25,,\r
"""
