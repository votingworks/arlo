"""
Views provide an interface to access scoped data based on a user's
permissions. The interface is intended to mimic SQLAlchemy's Model.query
interface, and returns SQLAlchemy query objects with the appropriate filters
pre-applied. Views should be the primary way that the database is queried. To
access unscoped data in special cases, use the unpermissioned_models module.
"""
# pylint: disable=invalid-name
from sqlalchemy.orm import aliased
from .models import *


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

    def __init__(self, election: Election):
        self.election = election

        self.JurisdictionAdministration_query = (
            JurisdictionAdministration.unpermissioned_query.join(aliased(Jurisdiction))
            .filter_by(election_id=election.id)
            .reset_joinpoint()
        )

        self.Contest_query = Contest.unpermissioned_query.filter_by(
            election_id=election.id
        )

        self.Jurisdiction_query = Jurisdiction.unpermissioned_query.filter_by(
            election_id=election.id
        )

        self.Batch_query = (
            Batch.unpermissioned_query.join(aliased(Jurisdiction))
            .filter_by(election_id=election.id)
            .reset_joinpoint()
        )

        self.SampledBallot_query = (
            SampledBallot.unpermissioned_query.join(aliased(Batch))
            .join(aliased(Jurisdiction))
            .filter_by(election_id=election.id)
            .reset_joinpoint()
        )

        self.SampledBallotDraw_query = (
            SampledBallotDraw.unpermissioned_query.join(aliased(Round))
            .filter_by(election_id=election.id)
            .reset_joinpoint()
        )

        self.BallotInterpretation_query = (
            BallotInterpretation.unpermissioned_query.join(aliased(Contest))
            .filter_by(election_id=election.id)
            .reset_joinpoint()
        )


class JurisdictionView:
    def __init__(self, jurisdiction: Jurisdiction):
        self.jurisdiction = jurisdiction
        # TODO add queries


class AuditBoardView:
    def __init__(self, audit_board: AuditBoard):
        self.audit_board = audit_board
        # TODO add queries


__all__ = ["ElectionView", "JurisdictionView", "AuditBoardView"]
