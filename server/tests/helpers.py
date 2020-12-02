import uuid, json, re
from datetime import datetime
from typing import Any, List, Union, Tuple
from flask.testing import FlaskClient
from werkzeug.wrappers import Response
from sqlalchemy.exc import IntegrityError

from ..auth.lib import UserType
from ..auth import lib as auth_lib
from ..database import db_session
from ..models import *  # pylint: disable=wildcard-import
from ..api.audit_boards import end_round


DEFAULT_AA_EMAIL = "admin@example.com"


def default_ja_email(election_id: str):
    return f"jurisdiction.admin-{election_id}@example.com"


def post_json(client: FlaskClient, url: str, obj=None) -> Any:
    return client.post(
        url,
        headers={"Content-Type": "application/json"},
        data=json.dumps(obj) if obj else None,
    )


def put_json(client: FlaskClient, url: str, obj) -> Any:
    return client.put(
        url, headers={"Content-Type": "application/json"}, data=json.dumps(obj)
    )


def assert_ok(rv: Response):
    __tracebackhide__ = True  # pylint: disable=unused-variable
    assert (
        rv.status_code == 200
    ), f"Expected status code 200, got {rv.status_code}, body: {rv.data}"
    assert json.loads(rv.data) == {"status": "ok"}


def set_logged_in_user(
    client: FlaskClient,
    user_type: UserType,
    user_key=DEFAULT_AA_EMAIL,
    from_superadmin=False,
):
    with client.session_transaction() as session:  # type: ignore
        auth_lib.set_loggedin_user(session, user_type, user_key, from_superadmin)


def clear_logged_in_user(client: FlaskClient):
    with client.session_transaction() as session:  # type: ignore
        auth_lib.clear_loggedin_user(session)


def set_superadmin(client: FlaskClient):
    with client.session_transaction() as session:  # type: ignore
        auth_lib.set_superadmin(session)


def clear_superadmin(client: FlaskClient):
    with client.session_transaction() as session:  # type: ignore
        auth_lib.clear_superadmin(session)


def create_user(email=DEFAULT_AA_EMAIL) -> User:
    try:
        with db_session.begin_nested():  # pylint: disable=no-member
            user = User(id=str(uuid.uuid4()), email=email, external_id=email)
            db_session.add(user)
        return user
    except IntegrityError:
        user = User.query.filter_by(email=email).first()
        return user


def create_org_and_admin(
    org_name: str = "Test Org", user_email: str = DEFAULT_AA_EMAIL
) -> Tuple[str, str]:
    org = Organization(id=str(uuid.uuid4()), name=org_name)
    db_session.add(org)
    audit_admin = create_user(user_email)
    db_session.add(audit_admin)
    admin = AuditAdministration(organization_id=org.id, user_id=audit_admin.id)
    db_session.add(admin)
    db_session.commit()
    return org.id, audit_admin.id


def create_jurisdiction_admin(jurisdiction_id: str, user_email: str) -> str:
    jurisdiction_admin = create_user(user_email)
    db_session.add(jurisdiction_admin)
    admin = JurisdictionAdministration(
        user_id=jurisdiction_admin.id, jurisdiction_id=jurisdiction_id
    )
    db_session.add(admin)
    db_session.commit()
    return str(jurisdiction_admin.id)


def create_jurisdiction(
    election_id: str, jurisdiction_name: str = "Test Jurisdiction",
):
    jurisdiction = Jurisdiction(
        id=str(uuid.uuid4()), election_id=election_id, name=jurisdiction_name
    )
    db_session.add(jurisdiction)
    db_session.commit()
    return jurisdiction


def create_jurisdiction_and_admin(
    election_id: str, jurisdiction_name: str, user_email: str,
) -> Tuple[str, str]:
    jurisdiction = create_jurisdiction(election_id, jurisdiction_name)
    ja_id = create_jurisdiction_admin(jurisdiction.id, user_email)
    return jurisdiction.id, ja_id


def create_election(
    client: FlaskClient,
    audit_name: str = None,
    audit_type: str = AuditType.BALLOT_POLLING,
    audit_math_type: str = AuditMathType.BRAVO,
    organization_id: str = None,
) -> str:
    rv = post_json(
        client,
        "/api/election",
        {
            "auditName": audit_name or f"Test Audit {datetime.now(timezone.utc)}",
            "auditType": audit_type,
            "auditMathType": audit_math_type,
            "organizationId": organization_id,
        },
    )
    result = json.loads(rv.data)
    if "electionId" not in result:
        raise Exception(f"No electionId in response: {rv.data}")
    return str(result["electionId"])


def audit_ballot(
    ballot: SampledBallot,
    contest_id: str,
    interpretation: Interpretation,
    choices: List[ContestChoice] = None,
    is_overvote: bool = False,
):
    # Make sure we don't try to audit this ballot twice for this contest
    if not any(i for i in ballot.interpretations if i.contest_id == contest_id):
        ballot.interpretations = list(ballot.interpretations) + [
            BallotInterpretation(
                ballot_id=ballot.id,
                contest_id=contest_id,
                interpretation=interpretation,
                selected_choices=choices or [],
                is_overvote=is_overvote,
            )
        ]
        ballot.status = BallotStatus.AUDITED


def run_audit_round(
    round_id: str, target_contest_id: str, contest_ids: List[str], vote_ratio: float
):
    round = Round.query.get(round_id)
    contest = Contest.query.get(target_contest_id)
    other_contest_ids = set(contest_ids) - {target_contest_id}
    ballot_draws = (
        SampledBallotDraw.query.filter_by(round_id=round_id)
        .join(SampledBallot)
        .join(Batch)
        .order_by(Batch.name, SampledBallot.ballot_position)
        .all()
    )
    winner_votes = int(vote_ratio * len(ballot_draws))
    for ballot_draw in ballot_draws[:winner_votes]:
        audit_ballot(
            ballot_draw.sampled_ballot,
            contest.id,
            Interpretation.VOTE,
            [contest.choices[0]],
        )
        for other_contest_id in other_contest_ids:
            audit_ballot(
                ballot_draw.sampled_ballot,
                other_contest_id,
                Interpretation.CONTEST_NOT_ON_BALLOT,
            )
    for ballot_draw in ballot_draws[winner_votes:]:
        audit_ballot(
            ballot_draw.sampled_ballot,
            contest.id,
            Interpretation.VOTE,
            [contest.choices[1]],
        )
        for other_contest_id in other_contest_ids:
            audit_ballot(
                ballot_draw.sampled_ballot,
                other_contest_id,
                Interpretation.CONTEST_NOT_ON_BALLOT,
            )
    end_round(round.election, round)
    db_session.commit()


DATETIME_REGEX = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2}.\d{6})?(\+\d\d:\d\d)?"
)


def scrub_datetime(string: str) -> str:
    return re.sub(DATETIME_REGEX, "DATETIME", string)


def assert_match_report(report_bytes: bytes, snapshot):
    report = report_bytes.decode("utf-8")
    snapshot.assert_match(scrub_datetime(report))


def assert_is_id(value):
    __tracebackhide__ = True  # pylint: disable=unused-variable
    assert isinstance(value, str)
    uuid.UUID(value, version=4)  # Will raise exception on non-UUID strings


def assert_is_date(value):
    """
    Asserts that a value is a string formatted as an ISO-8601 string
    specifically as formatted by `datetime.isoformat`. Not all
    ISO-8601 strings are supported.

    See https://docs.python.org/3.8/library/datetime.html#datetime.date.fromisoformat.
    """
    __tracebackhide__ = True  # pylint: disable=unused-variable
    assert isinstance(value, str)
    datetime.fromisoformat(value)


def assert_is_passphrase(value):
    __tracebackhide__ = True  # pylint: disable=unused-variable
    assert isinstance(value, str)
    assert re.match(r"[a-z]+-[a-z]+-[a-z]+-[a-z]+", value)


def asserts_startswith(prefix: str):
    def assert_startswith(value: str):
        __tracebackhide__ = True  # pylint: disable=unused-variable
        assert isinstance(value, str)
        assert value.startswith(
            prefix
        ), f"expected:\n\n{value}\n\nto start with: {prefix}"

    return assert_startswith


def compare_json(actual_json, expected_json):
    """
    Checks that a json blob (represented as a Python dict) is equal-ish to an
    expected dict. The expected dict can contain assertion functions in place of
    any non-deterministic values.
    """
    __tracebackhide__ = True  # pylint: disable=unused-variable

    def serialize_keypath(keypath: List[Union[str, int]]) -> str:
        return f"root{''.join([f'[{serialize_key(key)}]' for key in keypath])}"

    def serialize_key(key: Union[str, int]) -> str:
        return f'"{key}"' if isinstance(key, str) else f"{key}"

    def inner_compare_json(
        actual_json, expected_json, current_keypath: List[Union[str, int]]
    ):
        __tracebackhide__ = True  # pylint: disable=unused-variable
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
