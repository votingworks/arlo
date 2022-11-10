import io
import uuid, json, re
from datetime import datetime
from typing import Any, List, Union, Tuple, Optional
import logging
from flask.testing import FlaskClient
from werkzeug.wrappers import Response
from sqlalchemy.exc import IntegrityError

from ..auth.auth_helpers import UserType
from ..auth import auth_helpers
from ..database import db_session
from ..models import *  # pylint: disable=wildcard-import
from ..api.audit_boards import end_round


DEFAULT_SUPPORT_EMAIL = "support@example.org"
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


def patch_json(client: FlaskClient, url: str, obj) -> Any:
    return client.patch(
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
    from_support_user=False,
):
    with client.session_transaction() as session:  # type: ignore
        auth_helpers.set_loggedin_user(session, user_type, user_key, from_support_user)


def clear_logged_in_user(client: FlaskClient):
    with client.session_transaction() as session:  # type: ignore
        auth_helpers.clear_loggedin_user(session)


def set_support_user(client: FlaskClient, email: str):
    with client.session_transaction() as session:  # type: ignore
        auth_helpers.set_support_user(session, email)


def clear_support_user(client: FlaskClient):
    with client.session_transaction() as session:  # type: ignore
        auth_helpers.clear_support_user(session)


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
    org_name: str = None, user_email: str = DEFAULT_AA_EMAIL
) -> Tuple[str, str]:
    org = Organization(
        id=str(uuid.uuid4()), name=org_name or f"Test Org {datetime.now(timezone.utc)}"
    )
    db_session.add(org)
    aa_id = add_admin_to_org(org.id, user_email)
    db_session.commit()
    return org.id, aa_id


def add_admin_to_org(org_id: str, user_email: str):
    audit_admin = create_user(user_email)
    db_session.add(audit_admin)
    admin = AuditAdministration(organization_id=org_id, user_id=audit_admin.id)
    db_session.add(admin)
    db_session.commit()
    return audit_admin.id


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
    has_invalid_write_in: bool = False,
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
                has_invalid_write_in=has_invalid_write_in,
            )
        ]
        ballot.status = BallotStatus.AUDITED


def run_audit_round(
    round_id: str,
    target_contest_id: str,
    contest_ids: List[str],
    vote_ratio: float,
    invalid_write_in_ratio: float = 0,
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

    num_winner_votes = int(vote_ratio * len(ballot_draws))
    num_loser_votes = len(ballot_draws) - num_winner_votes
    num_winner_invalid_write_ins = int(invalid_write_in_ratio * num_winner_votes)
    num_loser_invalid_write_ins = int(invalid_write_in_ratio * num_loser_votes)

    for i, ballot_draw in enumerate(ballot_draws[:num_winner_votes]):
        audit_ballot(
            ballot_draw.sampled_ballot,
            contest.id,
            Interpretation.VOTE,
            [contest.choices[0]],
            has_invalid_write_in=(i < num_winner_invalid_write_ins),
        )
        for other_contest_id in other_contest_ids:
            audit_ballot(
                ballot_draw.sampled_ballot,
                other_contest_id,
                Interpretation.CONTEST_NOT_ON_BALLOT,
            )
    for i, ballot_draw in enumerate(ballot_draws[num_winner_votes:]):
        audit_ballot(
            ballot_draw.sampled_ballot,
            contest.id,
            Interpretation.VOTE,
            [contest.choices[1]],
            has_invalid_write_in=(i < num_loser_invalid_write_ins),
        )
        for other_contest_id in other_contest_ids:
            audit_ballot(
                ballot_draw.sampled_ballot,
                other_contest_id,
                Interpretation.CONTEST_NOT_ON_BALLOT,
            )
    end_round(round.election, round)
    db_session.commit()


def run_audit_round_all_blanks(
    round_id: str,
    target_contest_id: str,
    contest_ids: List[str],
    invalid_write_in_ratio: float = 0,
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

    num_invalid_write_ins = int(invalid_write_in_ratio * len(ballot_draws))

    for i, ballot_draw in enumerate(ballot_draws):
        audit_ballot(
            ballot_draw.sampled_ballot,
            contest.id,
            Interpretation.BLANK,
            [],
            has_invalid_write_in=(i < num_invalid_write_ins),
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

TEST_JURISDICTION_ADMIN_EMAIL_REGEX = re.compile(
    r"jurisdiction.admin-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}@example.com"
)


def scrub_datetime(string: str) -> str:
    return re.sub(DATETIME_REGEX, "DATETIME", string)


def scrub_test_jurisdiction_admin_email_uuid(string: str) -> str:
    return re.sub(
        TEST_JURISDICTION_ADMIN_EMAIL_REGEX,
        "jurisdiction.admin-UUID@example.com",
        string,
    )


def assert_match_report(report_bytes: bytes, snapshot):
    report = report_bytes.decode("utf-8")
    snapshot.assert_match(
        scrub_test_jurisdiction_admin_email_uuid(scrub_datetime(report))
    )


def assert_is_string(value):
    __tracebackhide__ = True  # pylint: disable=unused-variable
    assert isinstance(value, str)


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


def find_log(caplog, level: int, message: str) -> Optional[logging.LogRecord]:
    return next(
        (
            record
            for record in caplog.records
            if record.levelno == level and message in record.message
        ),
        None,
    )


def string_to_bytes_io(string: str) -> io.BytesIO:
    string_io = io.StringIO(string)
    bytes_io = io.BytesIO(string_io.read().encode("utf-8"))
    return bytes_io
