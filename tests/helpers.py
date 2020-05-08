import uuid, json, re
import pytest
import datetime
from typing import Any, List, Union, Tuple, Optional
from flask.testing import FlaskClient
from werkzeug.wrappers import Response
from sqlalchemy.orm import joinedload

from arlo_server.auth import (
    UserType,
    _USER,
    _SUPERADMIN,
)
from arlo_server.routes import create_organization
from arlo_server.models import (
    db,
    AuditAdministration,
    User,
    Jurisdiction,
    JurisdictionAdministration,
    Round,
    Contest,
    SampledBallot,
    SampledBallotDraw,
    BallotStatus,
    BallotInterpretation,
    Interpretation,
)
from arlo_server.audit_boards import end_round

SAMPLE_SIZE_ROUND_1 = 119  # Bravo sample size
J1_SAMPLES_ROUND_1 = 81
J1_SAMPLES_ROUND_2 = 280  # 90% probability sample size
AB1_BALLOTS_ROUND_1 = 50
AB2_BALLOTS_ROUND_1 = 25
AB1_BALLOTS_ROUND_2 = 150

DEFAULT_AA_EMAIL = "admin@example.com"
DEFAULT_JA_EMAIL = "jurisdiction.admin@example.com"


def post_json(client: FlaskClient, url: str, obj) -> Any:
    return client.post(
        url, headers={"Content-Type": "application/json"}, data=json.dumps(obj)
    )


def put_json(client: FlaskClient, url: str, obj) -> Any:
    return client.put(
        url, headers={"Content-Type": "application/json"}, data=json.dumps(obj)
    )


def assert_ok(rv: Response):
    __tracebackhide__ = True
    assert (
        rv.status_code == 200
    ), f"Expected status code 200, got {rv.status_code}, body: {rv.data}"
    assert json.loads(rv.data) == {"status": "ok"}


def set_logged_in_user(
    client: FlaskClient, user_type: UserType, user_key=DEFAULT_AA_EMAIL
):
    with client.session_transaction() as session:  # type: ignore
        session[_USER] = {"type": user_type, "key": user_key}


def clear_logged_in_user(client: FlaskClient):
    with client.session_transaction() as session:  # type: ignore
        session[_USER] = None


def set_superadmin(client: FlaskClient):
    with client.session_transaction() as session:  # type: ignore
        session[_SUPERADMIN] = True


def clear_superadmin(client: FlaskClient):
    with client.session_transaction() as session:  # type: ignore
        if _SUPERADMIN in session:
            del session[_SUPERADMIN]


def create_user(email=DEFAULT_AA_EMAIL) -> User:
    user = User(id=str(uuid.uuid4()), email=email, external_id=email)
    db.session.add(user)
    db.session.commit()
    return user


def create_org_and_admin(
    org_name: str = "Test Org", user_email: str = DEFAULT_AA_EMAIL
) -> Tuple[str, str]:
    org = create_organization(org_name)
    aa = create_user(user_email)
    db.session.add(aa)
    admin = AuditAdministration(organization_id=org.id, user_id=aa.id)
    db.session.add(admin)
    db.session.commit()
    return org.id, aa.id


def create_jurisdiction_admin(
    jurisdiction_id: str, user_email: str = DEFAULT_JA_EMAIL
) -> str:
    ja = create_user(user_email)
    db.session.add(ja)
    admin = JurisdictionAdministration(user_id=ja.id, jurisdiction_id=jurisdiction_id)
    db.session.add(admin)
    db.session.commit()
    return str(ja.id)


def create_jurisdiction_and_admin(
    election_id: str,
    jurisdiction_name: str = "Test Jurisdiction",
    user_email: str = DEFAULT_JA_EMAIL,
) -> Tuple[str, str]:
    jurisdiction = Jurisdiction(
        id=str(uuid.uuid4()), election_id=election_id, name=jurisdiction_name
    )
    db.session.add(jurisdiction)
    db.session.commit()
    ja_id = create_jurisdiction_admin(jurisdiction.id, user_email)
    return jurisdiction.id, ja_id


def create_election(
    client: FlaskClient,
    audit_name: str = "Test Audit",
    organization_id: str = None,
    is_multi_jurisdiction: bool = True,
) -> str:
    rv = post_json(
        client,
        "/election/new",
        {
            "auditName": audit_name,
            "organizationId": organization_id,
            "isMultiJurisdiction": is_multi_jurisdiction,
        },
    )
    result = json.loads(rv.data)
    if "electionId" not in result:
        raise Exception(f"No electionID in response: {rv.data}")
    return str(result["electionId"])


def audit_ballot(
    ballot: SampledBallot,
    contest_id: str,
    interpretation: Interpretation,
    choice_id: Optional[str] = None,
):
    if ballot.status != BallotStatus.AUDITED:
        db.session.add(
            BallotInterpretation(
                ballot_id=ballot.id,
                contest_id=contest_id,
                interpretation=interpretation,
                contest_choice_id=choice_id,
            )
        )
        ballot.status = BallotStatus.AUDITED


def run_audit_round(round_id: str, contest_id: str, vote_ratio: float):
    round = Round.query.options(
        joinedload(Round.sampled_ballot_draws).joinedload(
            SampledBallotDraw.sampled_ballot
        )
    ).get(round_id)
    contest = Contest.query.get(contest_id)
    winner_votes = int(vote_ratio * len(round.sampled_ballot_draws))
    for ballot_draw in round.sampled_ballot_draws[:winner_votes]:
        audit_ballot(
            ballot_draw.sampled_ballot,
            contest.id,
            Interpretation.VOTE,
            contest.choices[0].id,
        )
    for ballot_draw in round.sampled_ballot_draws[winner_votes:]:
        audit_ballot(
            ballot_draw.sampled_ballot,
            contest.id,
            Interpretation.VOTE,
            contest.choices[1].id,
        )
    end_round(round.election, round)
    db.session.commit()


def assert_is_id(x):
    __tracebackhide__ = True
    assert isinstance(x, str)
    uuid.UUID(x, version=4)  # Will raise exception on non-UUID strings


def assert_is_date(x):
    """
    Asserts that a value is a string formatted as an ISO-8601 string
    specifically as formatted by `datetime.datetime.isoformat`. Not all
    ISO-8601 strings are supported.
    
    See https://docs.python.org/3.8/library/datetime.html#datetime.date.fromisoformat.
    """
    __tracebackhide__ = True
    assert isinstance(x, str)
    datetime.datetime.fromisoformat(x)


def assert_is_passphrase(x):
    __tracebackhide__ = True
    assert isinstance(x, str)
    assert re.match(r"[a-z]+-[a-z]+-[a-z]+-[a-z]+", x)


def asserts_startswith(prefix: str):
    def assert_startswith(x: str):
        __tracebackhide__ = True
        assert isinstance(x, str)
        assert x.startswith(prefix), f"expected:\n\n{x}\n\nto start with: {prefix}"

    return assert_startswith


def compare_json(actual_json, expected_json):
    """
    Checks that a json blob (represented as a Python dict) is equal-ish to an
    expected dict. The expected dict can contain assertion functions in place of
    any non-deterministic values.
    """
    __tracebackhide__ = True

    def serialize_keypath(keypath: List[Union[str, int]]) -> str:
        return f"root{''.join([f'[{serialize_key(key)}]' for key in keypath])}"

    def serialize_key(key: Union[str, int]) -> str:
        return f'"{key}"' if isinstance(key, str) else f"{key}"

    def inner_compare_json(
        actual_json, expected_json, current_keypath: List[Union[str, int]]
    ):
        __tracebackhide__ = True
        if isinstance(expected_json, dict):
            assert isinstance(
                actual_json, dict
            ), f"expected dict, got {type(actual_json).__name__} at {serialize_keypath(current_keypath)}"
            for k, v in expected_json.items():
                inner_compare_json(actual_json[k], v, current_keypath + [k])
            assert (
                actual_json.keys() == expected_json.keys()
            ), f"dict keys do not match at {serialize_keypath(current_keypath)}"
        elif isinstance(expected_json, list):
            assert isinstance(
                actual_json, list
            ), f"expected list, got {type(actual_json).__name__} at {serialize_keypath(current_keypath)}"
            for i, v in enumerate(expected_json):
                inner_compare_json(actual_json[i], v, current_keypath + [i])
            assert len(actual_json) == len(
                expected_json
            ), f"list lengths do not match at {serialize_keypath(current_keypath)}"
        elif callable(expected_json):
            try:
                expected_json(actual_json)
            except Exception as error:
                raise AssertionError(
                    f"custom comparison failed at {serialize_keypath(current_keypath)}"
                ) from error
        else:
            assert (
                actual_json == expected_json
            ), f"Actual: {actual_json}\nExpected: {expected_json}\nKeypath: {serialize_keypath(current_keypath)}"

    inner_compare_json(actual_json, expected_json, [])


def test_compare_json():
    def asserts_gt(n: int):
        def assert_gt(value: int):
            assert isinstance(value, int)
            assert value > n

        return assert_gt

    compare_json([], [])
    compare_json({}, {})
    compare_json("a", "a")
    compare_json(1, 1)
    compare_json([1, {}], [1, {}])
    compare_json(1, asserts_gt(0))

    with pytest.raises(AssertionError, match=r"Actual: 1\nExpected: 2\nKeypath: root"):
        compare_json(1, 2)

    with pytest.raises(
        AssertionError, match=r'Actual: 1\nExpected: 2\nKeypath: root\["a"\]'
    ):
        compare_json({"a": 1}, {"a": 2})

    with pytest.raises(AssertionError, match=r"dict keys do not match at root"):
        compare_json({"a": 1}, {})

    with pytest.raises(AssertionError, match=r"expected dict, got list at root"):
        compare_json([], {})

    with pytest.raises(AssertionError, match=r"expected list, got dict at root"):
        compare_json({}, [])

    with pytest.raises(AssertionError, match=r"list lengths do not match at root"):
        compare_json([1], [])

    with pytest.raises(
        AssertionError, match=r"Actual: 2\nExpected: 3\nKeypath: root\[1\]"
    ):
        compare_json([1, 2], [1, 3])

    with pytest.raises(AssertionError, match=r"custom comparison failed at root"):
        compare_json(1, asserts_gt(1))

    with pytest.raises(AssertionError, match=r"custom comparison failed at root\[2\]"):
        compare_json([1, 2, 3], [asserts_gt(0), asserts_gt(1), asserts_gt(3)])
