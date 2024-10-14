import time
from datetime import datetime, timezone
from urllib.parse import urljoin
import requests

from .. import config
from ..models import ActivityLogRecord
from ..auth.auth_helpers import UserType
from ..database import db_session
from . import activity_log
from ..sentry import configure_sentry


# pylint: disable=too-many-return-statements
def slack_message(activity: activity_log.Activity):
    base = activity.base
    org_link = urljoin(config.HTTP_ORIGIN, f"/support/orgs/{base.organization_id}")
    org_context = dict(
        type="mrkdwn",
        text=f":flag-us: <{org_link}|{base.organization_name}>",
    )
    user_type = (
        {
            UserType.AUDIT_ADMIN: "Audit admin",
            UserType.JURISDICTION_ADMIN: "Jurisdiction admin",
            UserType.AUDIT_BOARD: "",  # We already put "Audit Board" in every audit board's name
        }[UserType(base.user_type)]
        if base.user_type
        else ""
    )
    user_name = (
        activity.audit_board_name
        if isinstance(activity, activity_log.AuditBoardSignOff)
        else base.user_key
    )
    user_context = dict(
        type="mrkdwn",
        text=(
            f":technologist: Support user {base.support_user_email} logged in as {user_type.lower()} {user_name}"
            if base.support_user_email
            else f":technologist: {user_type} {user_name}"
        ),
    )
    time_context = dict(
        type="mrkdwn",
        text=f":clock3: <!date^{int(activity.timestamp.timestamp())}^{{date_short}}, {{time_secs}}|{activity.timestamp.isoformat()}>",
    )

    audit_link = urljoin(config.HTTP_ORIGIN, f"/support/audits/{base.election_id}")
    assert base.audit_type
    audit_type = dict(
        BALLOT_POLLING="Ballot Polling",
        BALLOT_COMPARISON="Ballot Comparison",
        BATCH_COMPARISON="Batch Comparison",
        HYBRID="Hybrid",
    )[base.audit_type]
    audit_context = dict(
        type="mrkdwn",
        text=f":microscope: <{audit_link}|{base.audit_name}> ({audit_type})",
    )

    if isinstance(activity, activity_log.JurisdictionActivity):
        jurisdiction_link = urljoin(
            config.HTTP_ORIGIN, f"/support/jurisdictions/{activity.jurisdiction_id}"
        )
        jurisdiction_context = dict(
            type="mrkdwn",
            text=f":classical_building: <{jurisdiction_link}|{activity.jurisdiction_name}> ",
        )

    acting_user = base.support_user_email or base.user_key

    if isinstance(activity, activity_log.CreateAudit):
        return dict(
            text=f"{acting_user} created an audit: {base.audit_name} ({audit_type})",
            blocks=[
                dict(
                    type="section",
                    text=dict(
                        type="mrkdwn",
                        text=f"*{acting_user} created an audit: <{audit_link}|{base.audit_name}>* ({audit_type})",
                    ),
                ),
                dict(
                    type="context",
                    elements=[org_context, time_context, user_context],
                ),
            ],
        )

    if isinstance(activity, activity_log.DeleteAudit):
        return dict(
            text=f"{acting_user} deleted an audit: {base.audit_name} ({audit_type})",
            blocks=[
                dict(
                    type="section",
                    text=dict(
                        type="mrkdwn",
                        text=f"*{acting_user} deleted an audit: <{audit_link}|{base.audit_name}>* ({audit_type})",
                    ),
                ),
                dict(
                    type="context",
                    elements=[org_context, time_context, user_context],
                ),
            ],
        )

    if isinstance(activity, activity_log.StartRound):
        return dict(
            text=f"{acting_user} started round {activity.round_num}",
            blocks=[
                dict(
                    type="section",
                    text=dict(
                        type="mrkdwn",
                        text=f"*{acting_user} started round {activity.round_num}*",
                    ),
                ),
                dict(
                    type="context",
                    elements=[org_context, audit_context, time_context, user_context],
                ),
            ],
        )

    if isinstance(activity, activity_log.EndRound):
        audit_status = (
            "audit complete"
            if activity.is_audit_complete
            else "another round is needed"
        )
        return dict(
            text=f"Round {activity.round_num} ended, {audit_status}",
            blocks=[
                dict(
                    type="section",
                    text=dict(
                        type="mrkdwn",
                        text=f"*Round {activity.round_num} ended, {audit_status}*",
                    ),
                ),
                dict(
                    type="context",
                    elements=[org_context, audit_context, time_context],
                ),
            ],
        )

    if isinstance(activity, activity_log.CalculateSampleSizes):
        return dict(
            text=f"{acting_user} calculated sample sizes",
            blocks=[
                dict(
                    type="section",
                    text=dict(
                        type="mrkdwn", text=f"*{acting_user} calculated sample sizes*"
                    ),
                ),
                dict(
                    type="context",
                    elements=[org_context, audit_context, time_context, user_context],
                ),
            ],
        )

    if isinstance(activity, activity_log.UploadFile):
        file_type = dict(
            ballot_manifest="Ballot manifest",
            batch_inventory_cvrs="Batch inventory CVR",
            batch_inventory_tabulator_status="Batch inventory tabulator status",
            batch_tallies="Batch tallies",
            cvrs="CVR",
        )[activity.file_type]
        outcome = "failed" if activity.error else "succeeded"
        return dict(
            text=f"{file_type} upload {outcome} for {activity.jurisdiction_name}",
            blocks=list(
                filter(
                    lambda block: block,
                    [
                        dict(
                            type="section",
                            text=dict(
                                type="mrkdwn",
                                text=f"*{file_type} upload {outcome} for {activity.jurisdiction_name}*",
                            ),
                        ),
                        (
                            dict(
                                type="context",
                                elements=[
                                    dict(type="mrkdwn", text=f":x: {activity.error}")
                                ],
                            )
                            if activity.error
                            else None
                        ),
                        dict(
                            type="context",
                            elements=[
                                org_context,
                                jurisdiction_context,
                                audit_context,
                                time_context,
                                user_context,
                            ],
                        ),
                    ],
                )
            ),
        )

    if isinstance(activity, activity_log.CreateAuditBoards):
        s = "s" if activity.num_audit_boards > 1 else ""  # pylint: disable=invalid-name
        return dict(
            text=f"{activity.num_audit_boards} audit board{s} created for {activity.jurisdiction_name}",
            blocks=[
                dict(
                    type="section",
                    text=dict(
                        type="mrkdwn",
                        text=f"*{activity.num_audit_boards} audit boards created for {activity.jurisdiction_name}*",
                    ),
                ),
                dict(
                    type="context",
                    elements=[
                        org_context,
                        jurisdiction_context,
                        audit_context,
                        time_context,
                        user_context,
                    ],
                ),
            ],
        )

    if isinstance(activity, activity_log.RecordResults):
        return dict(
            text=f"Results recorded for {activity.jurisdiction_name}",
            blocks=[
                dict(
                    type="section",
                    text=dict(
                        type="mrkdwn",
                        text=f"*Results recorded for {activity.jurisdiction_name}*",
                    ),
                ),
                dict(
                    type="context",
                    elements=[
                        org_context,
                        jurisdiction_context,
                        audit_context,
                        time_context,
                        user_context,
                    ],
                ),
            ],
        )

    if isinstance(activity, activity_log.FinalizeBatchResults):
        return dict(
            text=f"Finalized batch results for {activity.jurisdiction_name}",
            blocks=[
                dict(
                    type="section",
                    text=dict(
                        type="mrkdwn",
                        text=f"*Finalized batch results for {activity.jurisdiction_name}*",
                    ),
                ),
                dict(
                    type="context",
                    elements=[
                        org_context,
                        jurisdiction_context,
                        audit_context,
                        time_context,
                        user_context,
                    ],
                ),
            ],
        )

    if isinstance(activity, activity_log.AuditBoardSignOff):
        return dict(
            text=f"{activity.audit_board_name} in {activity.jurisdiction_name} signed off",
            blocks=[
                dict(
                    type="section",
                    text=dict(
                        type="mrkdwn",
                        text=f"*{activity.audit_board_name} in {activity.jurisdiction_name} signed off*",
                    ),
                ),
                dict(
                    type="context",
                    elements=[
                        org_context,
                        jurisdiction_context,
                        audit_context,
                        time_context,
                        user_context,
                    ],
                ),
            ],
        )

    raise Exception(  # pragma: no cover
        f"slack_message not implemented for activity type: {activity.__class__.__name__}"
    )


# The optional organization_id parameter makes this function thread-safe for
# testing. Each test has its own org, and we don't want tests running in
# parallel to influence each other.
def send_new_slack_notification(organization_id: str = None) -> None:
    if config.SLACK_WEBHOOK_URL is None:
        raise Exception("Missing SLACK_WEBHOOK_URL")

    record = (
        ActivityLogRecord.query.filter(ActivityLogRecord.posted_to_slack_at.is_(None))
        .filter_by(**dict(organization_id=organization_id) if organization_id else {})
        .filter(ActivityLogRecord.activity_name != "JurisdictionAdminLogin")
        .order_by(ActivityLogRecord.timestamp)
        .limit(1)
        .one_or_none()
    )
    if record:
        ActivityClass = getattr(  # pylint: disable=invalid-name
            activity_log, record.activity_name
        )
        activity: activity_log.Activity = ActivityClass(
            **dict(
                record.info,
                base=activity_log.ActivityBase(**record.info["base"]),
                timestamp=record.timestamp,
            )
        )

        rv = requests.post(
            config.SLACK_WEBHOOK_URL,
            json=slack_message(activity),
            timeout=10,  # seconds
        )
        if rv.status_code != 200:
            raise Exception(f"Error posting record {record.id}:\n\n{rv.text}")

        record.posted_to_slack_at = datetime.now(timezone.utc)


if __name__ == "__main__":  # pragma: no cover
    configure_sentry()
    # We send at most one Slack notification per second, since that's what the
    # Slack API allows.
    while True:
        send_new_slack_notification()
        # We always commit the current transaction before sleeping, otherwise
        # we will have "idle in transaction" queries that will lock the
        # database, which gets in the way of migrations.
        db_session.commit()
        time.sleep(1)
