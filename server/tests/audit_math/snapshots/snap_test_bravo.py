# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots["test_ballot_polling_not_found_ballots 1"] = {
    ("cand1", "cand3"): 1.431846034590506e-06,
    ("cand2", "cand3"): 0.00016313261169996314,
}
