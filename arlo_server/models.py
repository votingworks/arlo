from enum import Enum
from datetime import datetime as dt
from sqlalchemy.orm import relationship, backref, validates
import sqlalchemy as sa
from flask_sqlalchemy import SQLAlchemy, Model
from flask_sqlalchemy.model import DefaultMeta


class Base(Model):
    created_at = sa.Column(sa.DateTime, default=dt.utcnow, nullable=False)
    updated_at = sa.Column(
        sa.DateTime, default=dt.utcnow, onupdate=dt.utcnow, nullable=False
    )


db = SQLAlchemy(model_class=Base)

# Typing workaround from https://github.com/dropbox/sqlalchemy-stubs/issues/76#issuecomment-595839159
BaseModel: DefaultMeta = db.Model

# on-delete-cascade is done in SQLAlchemy like this:
# https://stackoverflow.com/questions/5033547/sqlalchemy-cascade-delete


class Organization(BaseModel):
    id = db.Column(db.String(200), primary_key=True)
    name = db.Column(db.String(200), nullable=False)

    elections = relationship("Election", backref="organization", passive_deletes=True)


# Election is a slight misnomer - this model represents an audit.
class Election(BaseModel):
    id = db.Column(db.String(200), primary_key=True)
    # audit_name must be unique within each Organization
    audit_name = db.Column(db.String(200), nullable=False)
    # election_name can be the same across audits
    election_name = db.Column(db.String(200))
    state = db.Column(db.String(100))
    election_date = db.Column(db.Date)
    election_type = db.Column(db.String(200))
    meeting_date = db.Column(db.Date)
    risk_limit = db.Column(db.Integer)
    random_seed = db.Column(db.String(100))

    # an election is "online" if every ballot is entered online, vs. offline in a tally sheet.
    online = db.Column(db.Boolean, nullable=False, default=False)

    # False for our old single-jurisdiction flow,
    # True for our new multi-jurisdiction flow
    is_multi_jurisdiction = db.Column(db.Boolean, nullable=False)

    # Who does this election belong to?
    organization_id = db.Column(
        db.String(200), db.ForeignKey("organization.id", ondelete="cascade"),
    )

    frozen_at = db.Column(db.DateTime)

    jurisdictions = relationship(
        "Jurisdiction",
        backref="election",
        passive_deletes=True,
        order_by="Jurisdiction.name",
    )
    contests = relationship(
        "Contest", backref="election", passive_deletes=True, order_by="Contest.name",
    )
    rounds = relationship(
        "Round", backref="election", passive_deletes=True, order_by="Round.round_num"
    )

    jurisdictions_file_id = db.Column(
        db.String(200), db.ForeignKey("file.id", ondelete="set null")
    )
    jurisdictions_file = relationship("File")

    __table_args__ = (db.UniqueConstraint("organization_id", "audit_name"),)


# these are typically counties
class Jurisdiction(BaseModel):
    id = db.Column(db.String(200), primary_key=True)
    election_id = db.Column(
        db.String(200), db.ForeignKey("election.id", ondelete="cascade"), nullable=False
    )
    name = db.Column(db.String(200), nullable=False)
    manifest_num_ballots = db.Column(db.Integer)
    manifest_num_batches = db.Column(db.Integer)

    manifest_file_id = db.Column(
        db.String(200), db.ForeignKey("file.id", ondelete="set null")
    )
    manifest_file = relationship("File")

    batches = relationship("Batch", backref="jurisdiction", passive_deletes=True)
    audit_boards = relationship(
        "AuditBoard",
        backref="jurisdiction",
        passive_deletes=True,
        order_by="AuditBoard.name",
    )
    contests = relationship(
        "Contest", secondary="contest_jurisdiction", passive_deletes=True,
    )

    __table_args__ = (db.UniqueConstraint("election_id", "name"),)


class User(BaseModel):
    id = db.Column(db.String(200), primary_key=True)
    email = db.Column(db.String(200), unique=True, nullable=False)
    external_id = db.Column(db.String(200), unique=True)

    organizations = relationship("Organization", secondary="audit_administration")
    jurisdictions = relationship(
        "Jurisdiction", secondary="jurisdiction_administration"
    )

    @validates("email")
    def lowercase_email(self, _key, email):
        return email.lower()


class AuditAdministration(BaseModel):
    organization_id = db.Column(
        db.String(200),
        db.ForeignKey("organization.id", ondelete="cascade"),
        nullable=False,
    )
    user_id = db.Column(
        db.String(200), db.ForeignKey("user.id", ondelete="cascade"), nullable=False
    )

    organization = relationship(
        Organization,
        backref=backref("audit_administrations", cascade="all, delete-orphan"),
    )
    user = relationship(
        User, backref=backref("audit_administrations", cascade="all, delete-orphan")
    )

    __table_args__ = (db.PrimaryKeyConstraint("organization_id", "user_id"),)


class JurisdictionAdministration(BaseModel):
    user_id = db.Column(
        db.String(200), db.ForeignKey("user.id", ondelete="cascade"), nullable=False
    )
    jurisdiction_id = db.Column(
        db.String(200),
        db.ForeignKey("jurisdiction.id", ondelete="cascade"),
        nullable=False,
    )

    jurisdiction = relationship(
        Jurisdiction,
        backref=backref("jurisdiction_administrations", cascade="all, delete-orphan"),
    )
    user = relationship(
        User,
        backref=backref("jurisdiction_administrations", cascade="all, delete-orphan"),
    )

    __table_args__ = (db.PrimaryKeyConstraint("user_id", "jurisdiction_id"),)


class Batch(BaseModel):
    id = db.Column(db.String(200), primary_key=True)
    jurisdiction_id = db.Column(
        db.String(200),
        db.ForeignKey("jurisdiction.id", ondelete="cascade"),
        nullable=False,
    )
    name = db.Column(db.String(200), nullable=False)
    num_ballots = db.Column(db.Integer, nullable=False)
    storage_location = db.Column(db.String(200))
    tabulator = db.Column(db.String(200))

    ballots = relationship("SampledBallot", backref="batch", passive_deletes=True)

    __table_args__ = (db.UniqueConstraint("jurisdiction_id", "name"),)


class Contest(BaseModel):
    id = db.Column(db.String(200), primary_key=True)
    election_id = db.Column(
        db.String(200), db.ForeignKey("election.id", ondelete="cascade"), nullable=False
    )
    name = db.Column(db.String(200), nullable=False)
    # is_targeted = True for targeted contests, False for opportunistic contests
    is_targeted = db.Column(db.Boolean, nullable=False)
    total_ballots_cast = db.Column(db.Integer, nullable=False)
    num_winners = db.Column(db.Integer, nullable=False)
    votes_allowed = db.Column(db.Integer, nullable=False)

    choices = relationship(
        "ContestChoice",
        backref="contest",
        passive_deletes=True,
        order_by="ContestChoice.name",
    )
    results = relationship(
        "RoundContestResult", backref="contest", passive_deletes=True
    )
    jurisdictions = relationship(
        "Jurisdiction",
        secondary="contest_jurisdiction",
        order_by="Jurisdiction.name",
        passive_deletes=True,
    )


class ContestChoice(BaseModel):
    id = db.Column(db.String(200), primary_key=True)
    contest_id = db.Column(
        db.String(200), db.ForeignKey("contest.id", ondelete="cascade"), nullable=False,
    )
    name = db.Column(db.String(200), nullable=False)
    num_votes = db.Column(db.Integer, nullable=False)

    results = relationship(
        "RoundContestResult", backref="contest_choice", passive_deletes=True
    )


contest_jurisdiction = db.Table(
    "contest_jurisdiction",
    db.Column(
        "contest_id",
        db.String(200),
        db.ForeignKey("contest.id", primary_key=True, ondelete="cascade"),
        nullable=False,
    ),
    db.Column(
        "jurisdiction_id",
        db.String(200),
        db.ForeignKey("jurisdiction.id", primary_key=True, ondelete="cascade"),
        nullable=False,
    ),
)


# TODO we should use this enum in the AuditBoard schema, but that would require
# a data model change and db migration
class Affiliation(str, Enum):
    DEMOCRAT = "DEM"
    REPUBLICAN = "REP"
    LIBERTARIAN = "LIB"
    INDEPENDENT = "IND"
    OTHER = "OTH"


class AuditBoard(BaseModel):
    id = db.Column(db.String(200), primary_key=True)
    jurisdiction_id = db.Column(
        db.String(200),
        db.ForeignKey("jurisdiction.id", ondelete="cascade"),
        nullable=False,
    )
    round_id = db.Column(db.String(200), db.ForeignKey("round.id", ondelete="cascade"))

    name = db.Column(db.String(200))
    member_1 = db.Column(db.String(200))
    member_1_affiliation = db.Column(db.String(200))
    member_2 = db.Column(db.String(200))
    member_2_affiliation = db.Column(db.String(200))
    passphrase = db.Column(db.String(1000), unique=True)
    signed_off_at = db.Column(db.DateTime)

    sampled_ballots = relationship(
        "SampledBallot",
        backref="audit_board",
        passive_deletes=True,
        order_by="SampledBallot.id",
    )

    __table_args__ = (db.UniqueConstraint("jurisdiction_id", "round_id", "name"),)


class Round(BaseModel):
    id = db.Column(db.String(200), primary_key=True)
    election_id = db.Column(
        db.String(200), db.ForeignKey("election.id", ondelete="cascade"), nullable=False
    )
    round_num = db.Column(db.Integer, nullable=False)
    ended_at = db.Column(db.DateTime)

    __table_args__ = (db.UniqueConstraint("election_id", "round_num"),)

    round_contests = relationship("RoundContest", backref="round", passive_deletes=True)
    sampled_ballot_draws = relationship(
        "SampledBallotDraw", backref="round", passive_deletes=True
    )
    audit_boards = relationship("AuditBoard", backref="round", passive_deletes=True)


class BallotStatus(str, Enum):
    NOT_AUDITED = "NOT_AUDITED"
    AUDITED = "AUDITED"
    NOT_FOUND = "NOT_FOUND"


# Represents a physical ballot. A ballot only gets interpreted by an audit
# board once per audit.
class SampledBallot(BaseModel):
    id = db.Column(db.String(200), primary_key=True)

    batch_id = db.Column(
        db.String(200), db.ForeignKey("batch.id", ondelete="cascade"), nullable=False
    )
    # this ballot position should be 1-indexed
    ballot_position = db.Column(db.Integer, nullable=False)

    __table_args__ = (db.UniqueConstraint("batch_id", "ballot_position"),)

    draws = relationship(
        "SampledBallotDraw", backref="sampled_ballot", passive_deletes=True
    )

    audit_board_id = db.Column(
        db.String(200), db.ForeignKey("audit_board.id", ondelete="cascade"),
    )
    status = db.Column(db.Enum(BallotStatus), nullable=False)
    interpretations = relationship(
        "BallotInterpretation", cascade="all, delete-orphan", passive_deletes=True
    )


# Represents one sampling of a ballot in a specific round. A ballot can get
# drawn multiple times per round, so a ticket number is assigned to identify
# each draw.
class SampledBallotDraw(BaseModel):
    ballot_id = db.Column(
        db.String(200),
        db.ForeignKey("sampled_ballot.id", ondelete="cascade"),
        nullable=False,
    )
    round_id = db.Column(
        db.String(200), db.ForeignKey("round.id", ondelete="cascade"), nullable=False
    )
    ticket_number = db.Column(db.String(200), nullable=False)

    __table_args__ = (
        db.PrimaryKeyConstraint("ballot_id", "round_id", "ticket_number"),
    )


class Interpretation(str, Enum):
    BLANK = "BLANK"
    CANT_AGREE = "CANT_AGREE"
    VOTE = "VOTE"


# Represents how the audit board interpreted the vote for a specific contest
# when they were auditing one ballot.
class BallotInterpretation(BaseModel):
    ballot_id = db.Column(
        db.String(200),
        db.ForeignKey("sampled_ballot.id", ondelete="cascade"),
        nullable=False,
    )
    contest_id = db.Column(
        db.String(200), db.ForeignKey("contest.id", ondelete="cascade"), nullable=False
    )

    __table_args__ = (db.PrimaryKeyConstraint("ballot_id", "contest_id"),)

    interpretation = db.Column(db.Enum(Interpretation), nullable=False)
    # If interpretation is VOTE, contest_choice_id holds the id for the choice
    # that was voted for. Otherwise null.
    contest_choice_id = db.Column(
        db.String(200), db.ForeignKey("contest_choice.id", ondelete="cascade")
    )
    comment = db.Column(db.Text)


class RoundContest(BaseModel):
    round_id = db.Column(
        db.String(200), db.ForeignKey("round.id", ondelete="cascade"), nullable=False
    )
    contest_id = db.Column(
        db.String(200), db.ForeignKey("contest.id", ondelete="cascade"), nullable=False,
    )

    sample_size_options = db.Column(db.String(1000))

    results = relationship("RoundContestResult", passive_deletes=True)

    __table_args__ = (db.PrimaryKeyConstraint("round_id", "contest_id"),)

    end_p_value = db.Column(db.Float)
    is_complete = db.Column(db.Boolean)
    sample_size = db.Column(db.Integer)


class RoundContestResult(BaseModel):
    round_id = db.Column(
        db.String(200), db.ForeignKey("round.id", ondelete="cascade"), nullable=False
    )
    contest_id = db.Column(
        db.String(200), db.ForeignKey("contest.id", ondelete="cascade"), nullable=False,
    )
    __table_args__ = (
        db.PrimaryKeyConstraint("round_id", "contest_choice_id"),
        db.ForeignKeyConstraint(
            ["round_id", "contest_id"],
            ["round_contest.round_id", "round_contest.contest_id"],
            ondelete="cascade",
        ),
    )

    contest_choice_id = db.Column(
        db.String(200),
        db.ForeignKey("contest_choice.id", ondelete="cascade"),
        nullable=False,
    )
    result = db.Column(db.Integer, nullable=False)


class File(BaseModel):
    id = db.Column(db.String(200), primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    contents = db.Column(db.Text, nullable=False)
    uploaded_at = db.Column(db.DateTime, nullable=False)

    # Metadata for processing files in the background.
    processing_started_at = db.Column(db.DateTime)
    processing_completed_at = db.Column(db.DateTime)
    processing_error = db.Column(db.Text)


class ProcessingStatus(str, Enum):
    READY_TO_PROCESS = "READY_TO_PROCESS"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    ERRORED = "ERRORED"


class USState(str, Enum):
    Alabama = "AL"
    Alaska = "AK"
    Arizona = "AZ"
    Arkansas = "AR"
    California = "CA"
    Colorado = "CO"
    Connecticut = "CT"
    Delaware = "DE"
    Florida = "FL"
    Georgia = "GA"
    Hawaii = "HI"
    Idaho = "ID"
    Illinois = "IL"
    Indiana = "IN"
    Iowa = "IA"
    Kansas = "KS"
    Kentucky = "KY"
    Louisiana = "LA"
    Maine = "ME"
    Maryland = "MD"
    Massachusetts = "MA"
    Michigan = "MI"
    Minnesota = "MN"
    Mississippi = "MS"
    Missouri = "MO"
    Montana = "MT"
    Nebraska = "NE"
    Nevada = "NV"
    NewHampshire = "NH"
    NewJersey = "NJ"
    NewMexico = "NM"
    NewYork = "NY"
    NorthCarolina = "NC"
    NorthDakota = "ND"
    Ohio = "OH"
    Oklahoma = "OK"
    Oregon = "OR"
    Pennsylvania = "PA"
    RhodeIsland = "RI"
    SouthCarolina = "SC"
    SouthDakota = "SD"
    Tennessee = "TN"
    Texas = "TX"
    Utah = "UT"
    Vermont = "VT"
    Virginia = "VA"
    Washington = "WA"
    WestVirginia = "WV"
    Wisconsin = "WI"
    Wyoming = "WY"
    DistrictOfColumbia = "DC"
    MarshallIslands = "MH"
    ArmedForcesAfrica = "AE"
    ArmedForcesAmericas = "AA"
    ArmedForcesCanada = "AE"
    ArmedForcesEurope = "AE"
    ArmedForcesMiddleEast = "AE"
    ArmedForcesPacific = "AP"
