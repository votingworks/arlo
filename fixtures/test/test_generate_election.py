import json
import pytest
from ..generate_election import *  # pylint: disable=wildcard-import


# Each test needs its own seeded RNG since the tests may run in any order, so we
# can't depend on a single RNG across all tests.
@pytest.fixture
def rand():
    return random.Random(0)


def test_random_numbers_that_sum_to_total(snapshot, rand):
    for total in range(0, 100, 10):
        for num_numbers in range(1, 10):
            result = random_numbers_that_sum_to_total(total, num_numbers, rand)
            assert sum(result) == total
            assert len(result) == num_numbers
            assert all(number >= 0 for number in result)

    assert pytest.raises(ValueError, random_numbers_that_sum_to_total, 0, 0, rand)
    assert random_numbers_that_sum_to_total(0, 1, rand) == [0]
    assert random_numbers_that_sum_to_total(0, 2, rand) == [0, 0]
    assert random_numbers_that_sum_to_total(1, 1, rand) == [1]

    # Since we're using a fixed seed, the results should be deterministic
    snapshot.assert_match(random_numbers_that_sum_to_total(100, 10, rand))
    snapshot.assert_match(random_numbers_that_sum_to_total(15, 2, rand))


def assert_is_valid_jurisdiction_tallies(
    tallies: Dict[str, JurisdictionTallies], election_spec: ElectionSpec
):
    assert list(tallies.keys()) == [
        jurisdiction["name"] for jurisdiction in election_spec["jurisdictions"]
    ]
    for contest in election_spec["contests"]:
        for choice_name, votes in contest["tally"].items():
            # Votes should add up across jurisdictions
            assert votes == sum(
                jurisdiction_tally[contest["name"]]["tally"][choice_name]
                for jurisdiction_tally in tallies.values()
                if contest["name"] in jurisdiction_tally
            )
        # Invalid votes should add up as well
        total_votes = sum(contest["tally"].values())
        invalid_votes = contest["total_ballots_cast"] - total_votes
        assert invalid_votes == sum(
            jurisdiction_tally[contest["name"]]["invalid_votes"]
            for jurisdiction_tally in tallies.values()
            if contest["name"] in jurisdiction_tally
        )


def assert_is_valid_cvrs(cvrs: List[Ballot], tallies: JurisdictionTallies):
    for contest_name, tally in tallies.items():
        cvrs_for_contest = [cvr for cvr in cvrs if contest_name in cvr["votes"]]
        # Should have a CVR for each ballot cast
        assert (
            len(cvrs_for_contest)
            == sum(tally["tally"].values()) + tally["invalid_votes"]
        )
        # Votes should add up across valid vote CVRs for each choice
        votes_allowed = 1  # For now, we only support one vote per contest
        valid_vote_cvrs = [
            cvr
            for cvr in cvrs_for_contest
            if sum(cvr["votes"][contest_name].values()) == votes_allowed
        ]
        for choice_name, votes in tally["tally"].items():
            assert votes == sum(
                cvr["votes"][contest_name][choice_name] for cvr in valid_vote_cvrs
            )
        # Invalid votes should add up as well
        invalid_vote_cvrs = [
            cvr
            for cvr in cvrs_for_contest
            if sum(cvr["votes"][contest_name].values()) != votes_allowed
        ]
        assert len(invalid_vote_cvrs) == tally["invalid_votes"]


def assert_is_valid_manifest(manifest: Manifest, cvrs: List[Ballot]):
    # Ballot counts should add up
    assert sum(num_ballots for _, num_ballots in manifest) == len(cvrs)


def assert_is_valid_batch_tallies(
    batch_tallies: BatchTallies,
    cvrs: List[Ballot],
    jurisdiction_tally: JurisdictionTally,
):
    # Should have all the batches
    assert {batch_name for batch_name, _ in batch_tallies} == {
        cvr["batch"]["name"] for cvr in cvrs
    }
    # Tallies should add up to the contest totals
    for choice_name, votes in jurisdiction_tally["tally"].items():
        assert sum(tally[choice_name] for _, tally in batch_tallies) == votes


# We snapshot the results of generating fixtures for this simple election to
# ensure that the exact calculations stay correct.
def test_simple_election(snapshot, rand):
    simple_election_spec: ElectionSpec = {
        "name": "Simple Election",
        "contests": [
            ContestSpec(
                name="Contest 1",
                number_of_winners=1,
                votes_allowed=1,
                total_ballots_cast=20,
                tally={"Candidate 1": 15, "Candidate 2": 3, "Candidate 3": 0},
                jurisdictions=["Jurisdiction 1", "Jurisdiction 2"],
            ),
        ],
        "jurisdictions": [
            JurisdictionSpec(name="Jurisdiction 1"),
            JurisdictionSpec(name="Jurisdiction 2"),
            JurisdictionSpec(name="Jurisdiction 3"),
        ],
    }

    jurisdiction_tallies = split_contest_tallies_across_jurisdictions(
        simple_election_spec, rand
    )
    assert_is_valid_jurisdiction_tallies(jurisdiction_tallies, simple_election_spec)
    snapshot.assert_match(jurisdiction_tallies)

    for tallies in jurisdiction_tallies.values():
        cvrs = list(generate_cvrs(tallies, simple_election_spec["contests"], rand))
        assert_is_valid_cvrs(cvrs, tallies)
        snapshot.assert_match(cvrs)

        manifest = cvrs_to_manifest(cvrs)
        assert_is_valid_manifest(manifest, cvrs)
        snapshot.assert_match(manifest)

        for contest in simple_election_spec["contests"]:
            if contest["name"] in tallies:
                batch_tallies = cvrs_to_batch_tallies(cvrs, contest)
                assert_is_valid_batch_tallies(
                    batch_tallies, cvrs, tallies[contest["name"]]
                )
                snapshot.assert_match(batch_tallies)


# We don't snapshot the results of generating fixtures for this election, since
# we may want to change the spec for other reasons. However, we can still check
# that the resulting data is valid (using property assertions). It's important
# to test this election because there are edge cases that only show up at a
# slightly larger scale than the simple election above (e.g. using multiple
# contests, larger numbers of ballots).
def test_small_election(rand):
    small_election_spec_path = os.path.join(
        os.path.dirname(__file__), "../small-election/small-election.spec.json"
    )
    with open(
        small_election_spec_path, "r", encoding="utf8"
    ) as small_election_spec_file:
        small_election_spec = json.loads(small_election_spec_file.read())

    jurisdiction_tallies = split_contest_tallies_across_jurisdictions(
        small_election_spec, rand
    )
    assert_is_valid_jurisdiction_tallies(jurisdiction_tallies, small_election_spec)

    for tallies in jurisdiction_tallies.values():
        cvrs = list(generate_cvrs(tallies, small_election_spec["contests"], rand))
        assert_is_valid_cvrs(cvrs, tallies)

        manifest = cvrs_to_manifest(cvrs)
        assert_is_valid_manifest(manifest, cvrs)

        for contest in small_election_spec["contests"]:
            if contest["name"] in tallies:
                batch_tallies = cvrs_to_batch_tallies(cvrs, contest)
                assert_is_valid_batch_tallies(
                    batch_tallies, cvrs, tallies[contest["name"]]
                )
