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

snapshots["test_unauditable_ballots 1"] = {
    "U": GenericRepr("Decimal('4.545454545454545454545454545')"),
    "U_without_unauditable_ballots": GenericRepr("Decimal('4.5')"),
}

snapshots["test_unauditable_ballots 2"] = {
    "computed_p": 0.474552,
    "computed_p_without_unauditable_ballots": 0.47050754458161864,
}
