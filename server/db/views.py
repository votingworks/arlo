"""
Views provide an interface to access scoped data based on a user's
permissions. The interface is intended to mimic SQLAlchemy's Model.query
interface, and returns SQLAlchemy query objects with the appropriate filters
pre-applied. Views should be the primary way that the database is queried. To
access unscoped data in special cases, use the unpermissioned_models module.
"""
# pylint: disable=invalid-name
from typing import TypeVar
from sqlalchemy.orm import aliased
from . import unpermissioned_models as m  # pylint: disable=wildcard-import


# Implementation note: For queries where we need to join, we used aliased()
# around the joined model so that users of the view can join in that model
# again without having a conflict from trying to join the same table twice. We
# call reset_joinpoint() at the end so that filters/joins appended to the query
# reference the original model, not the most recently joined model.


class ElectionView:
    """
    ElectionView is an interface to query database models scoped to the given
    election_id.
    """

    def __init__(self, election: m.Election):
        self.election = election

        self.Contest_query = m.Contest.query.filter_by(election_id=election.id)

        self.Jurisdiction_query = m.Jurisdiction.query.filter_by(
            election_id=election.id
        )

        self.Batch_query = (
            m.Batch.query.join(aliased(m.Jurisdiction))
            .filter_by(election_id=election.id)
            .reset_joinpoint()
        )

        self.SampledBallot_query = (
            m.SampledBallot.query.join(aliased(m.Batch))
            .join(aliased(m.Jurisdiction))
            .filter_by(election_id=election.id)
            .reset_joinpoint()
        )

        self.SampledBallotDraw_query = (
            m.SampledBallotDraw.query.join(aliased(m.Round))
            .filter_by(election_id=election.id)
            .reset_joinpoint()
        )

        self.BallotInterpretation_query = (
            m.BallotInterpretation.query.join(aliased(m.Contest))
            .filter_by(election_id=election.id)
            .reset_joinpoint()
        )


class JurisdictionView:
    def __init__(self, jurisdiction: m.Jurisdiction):
        self.jurisdiction = jurisdiction
        # TODO add queries


class AuditBoardView:
    def __init__(self, audit_board: m.AuditBoard):
        self.audit_board = audit_board
        # TODO add queries


class t:
    """
    t holds type variables for the SQLAlchemy models. This allows consumers
    of views to type functions that consume instances of the models without
    exposing the model classes directly.
    """

    Jurisdiction = TypeVar("Jurisdiction", bound=m.Jurisdiction)
    AuditBoard = TypeVar("AuditBoard", bound=m.AuditBoard)


__all__ = ["ElectionView", "JurisdictionView", "AuditBoardView", "t"]
