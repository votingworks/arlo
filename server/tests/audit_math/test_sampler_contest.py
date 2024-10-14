# pylint: disable=invalid-name,consider-using-dict-items,consider-using-f-string
import pytest

from ...audit_math.sampler_contest import Contest


@pytest.fixture
def contests():
    contests = []

    for contest in bravo_contests:
        contests.append(Contest(contest, bravo_contests[contest]))

    return contests


def test_compute_margins(contests):
    for contest in contests:
        true_margins_for_contest = true_margins[contest.name]
        computed_margins_for_contest = contest.margins

        for winner in true_margins_for_contest["winners"]:
            expected = round(true_margins_for_contest["winners"][winner]["p_w"], 5)
            computed = round(computed_margins_for_contest["winners"][winner]["p_w"], 5)
            assert expected == computed, "{} p_w failed: got {}, expected {}".format(
                contest.name, computed, expected
            )

            expected = round(true_margins_for_contest["winners"][winner]["s_w"], 5)
            computed = round(computed_margins_for_contest["winners"][winner]["s_w"], 5)
            assert expected == computed, "{} s_w failed: got {}, expected {}".format(
                contest.name, computed, expected
            )

            for cand in true_margins_for_contest["winners"][winner]["swl"]:
                expected = round(
                    true_margins_for_contest["winners"][winner]["swl"][cand], 5
                )
                computed = round(
                    computed_margins_for_contest["winners"][winner]["swl"][cand], 5
                )
                assert (
                    expected == computed
                ), "{} swl failed: got {}, expected {}".format(
                    contest.name, computed, expected
                )

        for loser in true_margins_for_contest["losers"]:
            expected = round(true_margins_for_contest["losers"][loser]["p_l"], 5)
            computed = round(computed_margins_for_contest["losers"][loser]["p_l"], 5)
            assert expected == computed, "{} p_l failed: got {}, expected {}".format(
                contest.name, computed, expected
            )

            expected = round(true_margins_for_contest["losers"][loser]["s_l"], 5)
            computed = round(computed_margins_for_contest["losers"][loser]["s_l"], 5)
            assert expected == computed, "{} s_l failed: got {}, expected {}".format(
                contest.name, computed, expected
            )


def test_diluted_margin(contests):
    for contest in contests:
        assert (
            contest.diluted_margin == true_dms[contest.name]
        ), "Diluted margin calculation failed! Got {}, expected {} for contest {}".format(
            contest.diluted_margin, true_dms[contest.name], contest.name
        )


def test_repr(contests):
    str_rep = str(contests[0])

    expected = "Contest(test1): numWinners: 1, votesAllowed: 1, total ballots: 1000, candidates: {'cand1': 600, 'cand2': 400}"

    assert str_rep == expected, "String representation is wrong!"


bravo_contests = {
    "test1": {
        "cand1": 600,
        "cand2": 400,
        "ballots": 1000,
        "numWinners": 1,
        "votesAllowed": 1,
    },
    "test2": {
        "cand1": 600,
        "cand2": 200,
        "cand3": 100,
        "ballots": 900,
        "votesAllowed": 1,
        "numWinners": 1,
    },
    "test3": {"cand1": 100, "ballots": 100, "votesAllowed": 1, "numWinners": 1},
    "test4": {"cand1": 100, "ballots": 100, "votesAllowed": 1, "numWinners": 1},
    "test5": {
        "cand1": 500,
        "cand2": 500,
        "ballots": 1000,
        "votesAllowed": 1,
        "numWinners": 1,
    },
    "test6": {
        "cand1": 300,
        "cand2": 200,
        "cand3": 200,
        "ballots": 1000,
        "votesAllowed": 1,
        "numWinners": 1,
    },
    "test7": {
        "cand1": 300,
        "cand2": 200,
        "cand3": 100,
        "ballots": 700,
        "votesAllowed": 1,
        "numWinners": 2,
    },
    "test8": {
        "cand1": 300,
        "cand2": 300,
        "cand3": 100,
        "ballots": 700,
        "votesAllowed": 1,
        "numWinners": 2,
    },
    "test9": {
        "cand1": 300,
        "cand2": 200,
        "ballots": 700,
        "votesAllowed": 1,
        "numWinners": 2,
    },
    "test10": {
        "cand1": 600,
        "cand2": 300,
        "cand3": 100,
        "ballots": 1000,
        "votesAllowed": 1,
        "numWinners": 2,
    },
}

true_margins = {
    "test1": {
        "winners": {"cand1": {"p_w": 0.6, "s_w": 0.6, "swl": {"cand2": 0.6}}},
        "losers": {"cand2": {"p_l": 0.4, "s_l": 0.4}},
    },
    "test2": {
        "winners": {
            "cand1": {
                "p_w": 2 / 3,
                "s_w": 2 / 3,
                "swl": {"cand2": 6 / 8, "cand3": 6 / 7},
            }
        },
        "losers": {
            "cand2": {"p_l": 2 / 9, "s_l": 2 / 9},
            "cand3": {"p_l": 1 / 9, "s_l": 1 / 9},
        },
    },
    "test3": {"winners": {"cand1": {"p_w": 1, "s_w": 1, "swl": {}}}, "losers": {}},
    "test4": {"winners": {"cand1": {"p_w": 1, "s_w": 1, "swl": {}}}, "losers": {}},
    "test5": {
        "winners": {"cand1": {"p_w": 0.5, "s_w": 0.5, "swl": {"cand2": 0.5}}},
        "losers": {"cand2": {"p_l": 0.5, "s_l": 0.5}},
    },
    "test6": {
        "winners": {
            "cand1": {
                "p_w": 0.3,
                "s_w": 300 / 700,
                "swl": {"cand2": 300 / (300 + 200), "cand3": 300 / (300 + 200)},
            }
        },
        "losers": {
            "cand2": {"p_l": 0.2, "s_l": 200 / 700},
            "cand3": {"p_l": 0.2, "s_l": 200 / 700},
        },
    },
    "test7": {
        "winners": {
            "cand1": {
                "p_w": 300 / 700,
                "s_w": 300 / 600,
                "swl": {"cand3": 300 / (300 + 100)},
            },
            "cand2": {
                "p_w": 200 / 700,
                "s_w": 200 / 600,
                "swl": {"cand3": 200 / (200 + 100)},
            },
        },
        "losers": {"cand3": {"p_l": 100 / 700, "s_l": 100 / 600}},
    },
    "test8": {
        "winners": {
            "cand1": {
                "p_w": 300 / 700,
                "s_w": 300 / 700,
                "swl": {"cand3": 300 / (300 + 100)},
            },
            "cand2": {
                "p_w": 300 / 700,
                "s_w": 300 / 700,
                "swl": {"cand3": 300 / (300 + 100)},
            },
        },
        "losers": {"cand3": {"p_l": 100 / 700, "s_l": 100 / 700}},
    },
    "test9": {
        "winners": {
            "cand1": {"p_w": 300 / 700, "s_w": 300 / 500, "swl": {}},
            "cand2": {"p_w": 200 / 700, "s_w": 200 / 500, "swl": {}},
        },
        "losers": {},
    },
    "test10": {
        "winners": {
            "cand1": {
                "p_w": 600 / 1000,
                "s_w": 600 / 1000,
                "swl": {"cand3": 600 / 700},
            },
            "cand2": {
                "p_w": 300 / 1000,
                "s_w": 300 / 1000,
                "swl": {"cand3": 300 / 400},
            },
        },
        "losers": {"cand3": {"p_l": 100 / 1000, "s_l": 100 / 1000}},
    },
}

true_dms = {
    "test1": 0.2,
    "test2": 4 / 9,
    "test3": -1,
    "test4": -1,
    "test5": 0,
    "test6": 0.1,
    "test7": 1 / 7,
    "test8": 2 / 7,
    "test9": -1,
    "test10": 0.2,
}
