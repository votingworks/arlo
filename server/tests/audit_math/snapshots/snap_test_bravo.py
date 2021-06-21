# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots["test_ballot_polling_not_found_ballots 1"] = {
    ("cand1", "cand3"): 1.431846034590505e-06,
    ("cand1", "cand4"): 1.2886614311314533e-05,
    ("cand2", "cand3"): 0.27430209050114257,
    ("cand2", "cand4"): 0.6171797036275707,
}
