# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import GenericRepr, Snapshot


snapshots = Snapshot()

snapshots["test_pending_ballots 1"] = GenericRepr(
    "Decimal('4.591836734693877551020408163')"
)

snapshots["test_pending_ballots 2"] = 0.47861956652949245

snapshots["test_pending_ballots 3"] = 0.48371126404576364
