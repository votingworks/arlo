# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots["test_draw_sample 1"] = [
    ("0.000617786129909912", ("pct 2", 3), 1),
    ("0.002991631653037245", ("pct 3", 24), 1),
    ("0.012057030610635061", ("pct 1", 25), 1),
    ("0.017930028930651931", ("pct 4", 19), 1),
    ("0.025599454926985137", ("pct 3", 15), 1),
    ("0.045351055354441163", ("pct 1", 7), 1),
    ("0.063913979803461405", ("pct 1", 8), 1),
    ("0.064553852798863609", ("pct 1", 22), 1),
    ("0.078998835671540970", ("pct 1", 20), 1),
    ("0.090240829778172783", ("pct 3", 12), 1),
    ("0.096136506157297637", ("pct 1", 20), 2),
    ("0.104280162683637014", ("pct 4", 17), 1),
    ("0.108948480696023984", ("pct 1", 25), 2),
    ("0.111195681310332785", ("pct 1", 4), 1),
    ("0.114438612046531251", ("pct 4", 3), 1),
    ("0.130457464320709301", ("pct 2", 1), 1),
    ("0.133484785501449819", ("pct 1", 12), 1),
    ("0.134519219670087860", ("pct 3", 20), 1),
    ("0.135840440920085144", ("pct 3", 10), 1),
    ("0.138772253094235762", ("pct 4", 20), 1),
]

snapshots["test_draw_more_samples 1"] = [
    ("0.000617786129909912", ("pct 2", 3), 1),
    ("0.002991631653037245", ("pct 3", 24), 1),
    ("0.012057030610635061", ("pct 1", 25), 1),
    ("0.017930028930651931", ("pct 4", 19), 1),
    ("0.025599454926985137", ("pct 3", 15), 1),
    ("0.045351055354441163", ("pct 1", 7), 1),
    ("0.063913979803461405", ("pct 1", 8), 1),
    ("0.064553852798863609", ("pct 1", 22), 1),
    ("0.078998835671540970", ("pct 1", 20), 1),
    ("0.090240829778172783", ("pct 3", 12), 1),
]

snapshots["test_draw_more_samples 2"] = [
    ("0.096136506157297637", ("pct 1", 20), 2),
    ("0.104280162683637014", ("pct 4", 17), 1),
    ("0.108948480696023984", ("pct 1", 25), 2),
    ("0.111195681310332785", ("pct 1", 4), 1),
    ("0.114438612046531251", ("pct 4", 3), 1),
    ("0.130457464320709301", ("pct 2", 1), 1),
    ("0.133484785501449819", ("pct 1", 12), 1),
    ("0.134519219670087860", ("pct 3", 20), 1),
    ("0.135840440920085144", ("pct 3", 10), 1),
    ("0.138772253094235762", ("pct 4", 20), 1),
]

snapshots["test_draw_macro_sample 1"] = [
    ("0.003875995", "pct 16", 1),
    ("0.011835450", "pct 2", 1),
    ("0.022865957", "pct 2", 2),
    ("0.035732442", "pct 3", 1),
    ("0.125751540", "pct 2", 3),
    ("0.136070319", "pct 18", 1),
    ("0.150306323", "pct 6", 1),
    ("0.176060218", "pct 4", 1),
    ("0.183200120", "pct 13", 1),
    ("0.191343085", "pct 18", 2),
]

snapshots["test_draw_more_macro_sample 1"] = [
    ("0.003875995", "pct 16", 1),
    ("0.011835450", "pct 2", 1),
    ("0.022865957", "pct 2", 2),
    ("0.035732442", "pct 3", 1),
    ("0.125751540", "pct 2", 3),
]

snapshots["test_draw_more_macro_sample 2"] = [
    ("0.136070319", "pct 18", 1),
    ("0.150306323", "pct 6", 1),
    ("0.176060218", "pct 4", 1),
    ("0.183200120", "pct 13", 1),
    ("0.191343085", "pct 18", 2),
]
