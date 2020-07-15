from typing import Dict
from sqlalchemy import event, sql
from sqlalchemy.orm import Query
from . import models
from .models import *  # pylint: disable=wildcard-import

# Every database query the app makes should be scoped to the audit for the
# logged-in user. This module registers an event listener with SQLAlchemy to
# check every database query to ensure that it is properly scoped.
#
# It checks that each query filters by either:
# - a primary key
# - election_id
# - a foreign key to a model that is related to Election
#
# In order to opt out of this check, a query can specify:
# .execution_options(query_across_elections=True)

# This dict defines which columns satisfy the requirement for each model. Note
# that primary keys do not need to be included - those are checked separately.
model_to_election_columns: Dict[Type[models.BaseModel], list] = {
    Election: [Election.organization_id, Election.jurisdictions_file_id],
    Organization: [],
    Jurisdiction: [Jurisdiction.election_id, Jurisdiction.manifest_file_id],
    Batch: [Batch.jurisdiction_id],
    Contest: [Contest.election_id],
    ContestChoice: [ContestChoice.contest_id],
    AuditBoard: [
        AuditBoard.jurisdiction_id,
        AuditBoard.round_id,
        AuditBoard.passphrase,
    ],
    Round: [Round.election_id],
    SampledBallot: [SampledBallot.batch_id, SampledBallot.audit_board_id],
    SampledBallotDraw: [
        SampledBallotDraw.ballot_id,
        SampledBallotDraw.round_id,
        SampledBallotDraw.contest_id,
    ],
    BallotInterpretation: [
        BallotInterpretation.ballot_id,
        BallotInterpretation.contest_id,
    ],
    RoundContest: [RoundContest.round_id, RoundContest.contest_id],
    RoundContestResult: [
        RoundContestResult.round_id,
        RoundContestResult.contest_id,
        RoundContestResult.contest_choice_id,
    ],
    File: [File.id],
    JurisdictionAdministration: [],
    AuditAdministration: [],
    User: [User.email],
}
all_models = {
    export
    for export in models.__dict__.values()
    if isinstance(export, type)
    and issubclass(export, models.BaseModel)
    and export != models.BaseModel
}
checked_models = set(model_to_election_columns.keys())
if checked_models != all_models:
    # pylint: disable=invalid-name
    missing_models = ",".join(m.__name__ for m in all_models - checked_models)
    raise Exception(f"Missing models from check_query_scope: {missing_models}")

# Basic global variable lock - Python's threading locks don't seem to work
# easily here. We need to make sure only one event handler can operate at a
# time because when we try to print query.statement, it triggers the handler
# again, leading to an infinite loop.
check_query_scope_lock = False  # pylint: disable=invalid-name

# pylint: disable=protected-access
@event.listens_for(Query, "before_compile")
def check_query_scope(query: Query):
    def criterion_contains_column(column):
        def side_equals_column(side):
            return (
                side.key == column.key
                and side.table.name == column.class_.__tablename__
            )

        return lambda criterion: side_equals_column(
            criterion.left
        ) or side_equals_column(criterion.right)

    def criterion_contains_primary_key(criterion):
        return criterion.left.primary_key or criterion.right.primary_key

    def check_criterion(criterion, check_fn):
        if criterion is None:
            return False
        if isinstance(criterion, sql.elements.BinaryExpression):
            return check_fn(criterion)
        return any(
            check_criterion(subcriterion, check_fn) for subcriterion in criterion
        )

    def query_filters_on_primary_key_or_election(query, model):
        return check_criterion(query._criterion, criterion_contains_primary_key) or any(
            check_criterion(query._criterion, criterion_contains_column(column))
            for column in model_to_election_columns[model]
        )

    # Allow a flag to bypass this check
    if query._execution_options.get("query_across_elections", False):  # type: ignore
        return

    # When you call .count(), SQLAlchemy turns your query into a subquery and
    # adds a "SELECT count(*) FROM subquery" around it. Both the subquery and
    # the wrapped query get passed to this event handler individually, but the
    # wrapped query doesn't have the data we need to analyze it. So we skip the
    # wrapped count query and just check the subquery.
    if isinstance(query.column_descriptions[0]["expr"], sql.functions.count):
        return

    global check_query_scope_lock  # pylint: disable=global-statement,invalid-name
    if not check_query_scope_lock:
        check_query_scope_lock = True

        queried_models = [c["entity"] for c in query.column_descriptions if c["entity"]]
        joined_models = [e.class_ for e in query._join_entities]  # type: ignore
        models = set(queried_models + joined_models)

        if models and not any(
            query_filters_on_primary_key_or_election(query, model) for model in models
        ):
            raise Exception(
                "Query must filter on primary key or one of the following columns:\n"
                + "\n".join(
                    ", ".join(str(m) for m in model_to_election_columns[model])
                    for model in models
                )
                + "\n\n"
                + str(query.statement)
            )

        check_query_scope_lock = False
