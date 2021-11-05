import numpy as np

from server.audit_math.sampler_contest import Contest
from server.audit_math.raire import compute_raire_assertions
from server.audit_math.raire_utils import NEBAssertion, NENAssertion

RAIRE_INPUT_DIR = "server/tests/audit_math/RaireData/Input/"
RAIRE_OUTPUT_DIR = "server/tests/audit_math/RaireData/Output/"


def compare_result(path, contests):
    expected = {}

    with open(path, "r") as exp:
        lines = exp.readlines()

        reading_contest = None

        contest = []
        for line in lines:
            if line.startswith("CONTEST"):
                if reading_contest:
                    sorted_contest = sorted(contest)
                    expected[reading_contest] = sorted_contest
                    contest = []

                reading_contest = line.split()[1].strip()
            else:
                contest.append(line.strip())

        expected[reading_contest] = sorted(contest)

    assert len(expected) == len(contests), "Number of contests wrong for {}".format(
        path
    )

    for contest, asrtns in expected.items():
        assert contest in contests, "Incorrect contests for {}".format(path)

        casrtns = contests[contest]

        assert len(asrtns) == len(casrtns), print(
            "Number of assertions different for {}, contest {}".format(path, contest)
        )

        assert asrtns == casrtns, print(
            "Assertions differ for {}, contest {}".format(path, contest)
        )


def run_test(input_file, output_file, agap):
    # Load test contest
    with open(input_file, "r") as data:
        lines = data.readlines()

        ncontests = int(lines[0])

        contests = {}
        winners = {}

        for i in range(ncontests):
            toks = lines[1 + i].strip().split(",")

            cid = toks[1]
            ncands = int(toks[2])

            # Not sure what votesAllowed is, but RAIRE won't access these
            # fields of the contest structure anyway.
            cands = {"ballots": 0, "numWinners": 1, "votesAllowed": 1}

            for j in range(ncands):
                cands[toks[3 + j]] = 0

            contests[cid] = cands
            winners[cid] = toks[-1]

        cvrs = {}
        result = {}

        for line in range(ncontests + 1, len(lines)):
            toks = lines[line].strip().split(",")

            cid = toks[0]
            bid = toks[1]
            prefs = toks[2:]

            if prefs != []:
                contests[cid][prefs[0]] += 1

            contests[cid]["ballots"] += 1

            ballot = {}
            for contest in contests[cid]:
                if contest in prefs:
                    idx = prefs.index(contest) + 1
                    ballot[contest] = idx
                else:
                    ballot[contest] = 0

            if not bid in cvrs:
                cvrs[bid] = {cid: ballot}
            else:
                cvrs[bid][cid] = ballot

        for contest, votes in contests.items():
            con = Contest(contest, votes)

            audit = compute_raire_assertions(
                con, cvrs, winners[contest], lambda m: 1 / m if m > 0 else np.inf, agap,
            )

            asrtns = []
            for assertion in audit:
                asrtns.append(str(assertion))

            sorted_asrtns = sorted(asrtns)
            result[contest] = sorted_asrtns

        compare_result(output_file, result)


def test_simple_contest():
    cvr1 = {"test_con": {"Ann": 1, "Sally": 3, "Bob": 2, "Mike": 4}}

    neb1 = NEBAssertion("test_con", "Bob", "Sally")
    neb2 = NEBAssertion("test_con", "Ann", "Sally")
    neb3 = NEBAssertion("test_con", "Sally", "Bob")

    nen1 = NENAssertion("test_con", "Sally", "Ann", ["Bob"])
    nen2 = NENAssertion("test_con", "Sally", "Mike", [])
    nen3 = NENAssertion("test_con", "Sally", "Mike", ["Bob", "Ann"])

    assert neb1.is_vote_for_winner(cvr1) == 0
    assert neb1.is_vote_for_loser(cvr1) == 0

    assert neb2.is_vote_for_winner(cvr1) == 1
    assert neb2.is_vote_for_loser(cvr1) == 0

    assert neb3.is_vote_for_winner(cvr1) == 0
    assert neb3.is_vote_for_loser(cvr1) == 1

    assert nen1.is_vote_for_winner(cvr1) == 0
    assert nen1.is_vote_for_loser(cvr1) == 1

    assert nen2.is_vote_for_winner(cvr1) == 0
    assert nen2.is_vote_for_loser(cvr1) == 0

    assert nen3.is_vote_for_winner(cvr1) == 1
    assert nen3.is_vote_for_loser(cvr1) == 0


def test_aspen_wrong_winner():
    input_file = RAIRE_INPUT_DIR + "SpecialCases/Aspen_2009_wrong_winner.raire"
    output_file = RAIRE_OUTPUT_DIR + "SpecialCases/Aspen_2009_wrong_winner.raire.out"
    agap = 0
    run_test(input_file, output_file, agap)


def test_berkeley_2010():
    input_file = RAIRE_INPUT_DIR + "Berkeley_2010.raire"
    output_file = RAIRE_OUTPUT_DIR + "Berkeley_2010.raire.out"
    agap = 0
    run_test(input_file, output_file, agap)
