# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots["test_draw_macro_full_hand_tally 1"] = [
    ("0.370405751560609643", ("Jx 1", "pct 1")),
    ("0.847430249189970028", ("Jx 1", "pct 2")),
    ("0.851346057402501613", ("Jx 1", "pct 3")),
    ("0.328034953571610594", ("Jx 1", "pct 4")),
]

snapshots["test_draw_macro_full_hand_tally 2"] = [
    ("0.847430249189970028", ("Jx 1", "pct 2")),
    ("0.851346057402501613", ("Jx 1", "pct 3")),
    ("0.328034953571610594", ("Jx 1", "pct 4")),
]

snapshots["test_draw_macro_full_hand_tally 3"] = [
    ("0.370405751560609643", ("Jx 1", "pct 1")),
    ("0.851346057402501613", ("Jx 1", "pct 3")),
]

snapshots["test_draw_macro_full_hand_tally 4"] = [
    ("0.370405751560609643", ("Jx 1", "pct 1")),
    ("0.851346057402501613", ("Jx 1", "pct 3")),
]

snapshots["test_draw_macro_multiple_contests 1"] = [
    ("0.202823455933455274", ("Jx 1", "pct 5")),
    ("0.328034953571610594", ("Jx 1", "pct 4")),
    ("0.855737281564352199", ("Jx 1", "pct 5")),
    ("0.096486566275573723", ("Jx 1", "pct 0")),
    ("0.634903028357318938", ("Jx 1", "pct 6")),
    ("0.642074320588256264", ("Jx 1", "pct 8")),
    ("0.835553892011720777", ("Jx 1", "pct 9")),
    ("0.697435332323894639", ("Jx 1", "pct 8")),
    ("0.879238100629436915", ("Jx 1", "pct 5")),
    ("0.847430249189970028", ("Jx 1", "pct 2")),
]

snapshots["test_draw_macro_sample 1"] = [
    ("0.642074320588256264", ("Jx 1", "pct 8")),
    ("0.634903028357318938", ("Jx 1", "pct 6")),
    ("0.697435332323894639", ("Jx 1", "pct 8")),
    ("0.096486566275573723", ("Jx 1", "pct 0")),
    ("0.835553892011720777", ("Jx 1", "pct 9")),
    ("0.9722586520568512638", ("Jx 1", "pct 14")),
    ("0.030338217960461852", ("Jx 1", "pct 18")),
    ("0.546393063883135848", ("Jx 1", "pct 17")),
    ("0.878526714305113154", ("Jx 1", "pct 8")),
    ("0.847430249189970028", ("Jx 1", "pct 2")),
]

snapshots["test_draw_more_macro_sample 1"] = [
    ("0.642074320588256264", ("Jx 1", "pct 8")),
    ("0.634903028357318938", ("Jx 1", "pct 6")),
    ("0.697435332323894639", ("Jx 1", "pct 8")),
    ("0.096486566275573723", ("Jx 1", "pct 0")),
    ("0.835553892011720777", ("Jx 1", "pct 9")),
]

snapshots["test_draw_more_macro_sample 2"] = [
    ("0.9722586520568512638", ("Jx 1", "pct 14")),
    ("0.030338217960461852", ("Jx 1", "pct 18")),
    ("0.546393063883135848", ("Jx 1", "pct 17")),
    ("0.878526714305113154", ("Jx 1", "pct 8")),
    ("0.847430249189970028", ("Jx 1", "pct 2")),
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
