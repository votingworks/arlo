import enum
from typing import Type
from datetime import datetime as dt
from werkzeug.exceptions import NotFound
from sqlalchemy import *  # pylint: disable=wildcard-import
from sqlalchemy.orm import relationship, backref, validates
from .database import Base  # pylint: disable=cyclic-import


class BaseModel(Base):
    __abstract__ = True
    created_at = Column(DateTime, default=dt.utcnow, nullable=False)
    updated_at = Column(DateTime, default=dt.utcnow, onupdate=dt.utcnow, nullable=False)


# on-delete-cascade is done in SQLAlchemy like this:
# https://stackoverflow.com/questions/5033547/sqlalchemy-cascade-delete


class Organization(BaseModel):
    id = Column(String(200), primary_key=True)
    name = Column(String(200), nullable=False)

    elections = relationship(
        "Election", back_populates="organization", passive_deletes=True
    )


class AuditType(str, enum.Enum):
    BALLOT_POLLING = "BALLOT_POLLING"
    BATCH_COMPARISON = "BATCH_COMPARISON"
    BALLOT_COMPARISON = "BALLOT_COMPARISON"


class BallotPollingType(str, enum.Enum):
    BRAVO = "BRAVO"


# Election is a slight misnomer - this model represents an audit.
class Election(BaseModel):
    id = Column(String(200), primary_key=True)
    # audit_name must be unique within each Organization
    audit_name = Column(String(200), nullable=False)
    audit_type = Column(Enum(AuditType), nullable=False)
    # election_name can be the same across audits
    election_name = Column(String(200))
    state = Column(String(100))
    risk_limit = Column(Integer)
    random_seed = Column(String(100))

    # An audit is "online" if each ballot's audit results are entered in Arlo
    # individually, vs. written in a tally sheet and then totaled before
    # submitting to Arlo.
    online = Column(Boolean, nullable=False)

    # Who does this election belong to?
    organization_id = Column(
        String(200), ForeignKey("organization.id", ondelete="cascade"), nullable=False
    )
    organization = relationship("Organization", back_populates="elections")

    jurisdictions = relationship(
        "Jurisdiction",
        back_populates="election",
        uselist=True,
        passive_deletes=True,
        order_by="Jurisdiction.name",
    )
    contests = relationship(
        "Contest",
        back_populates="election",
        uselist=True,
        passive_deletes=True,
        order_by="Contest.created_at",
    )
    rounds = relationship(
        "Round",
        back_populates="election",
        uselist=True,
        passive_deletes=True,
        order_by="Round.round_num",
    )

    # The jurisdictions file contains a list of jurisdictions participating in
    # the audit and emails for the admins of each jurisdiction. We use this to
    # create Jurisdictions and JAs.
    jurisdictions_file_id = Column(
        String(200), ForeignKey("file.id", ondelete="set null")
    )
    jurisdictions_file = relationship(
        "File",
        foreign_keys=[jurisdictions_file_id],
        single_parent=True,
        cascade="all, delete-orphan",
    )

    # The standardized contests file (only used in ballot comparison audits)
    # contains a list of all possible contests and the corresponding list of
    # jurisdictions for those contests. The AA will select some of these
    # contests to target in the audit.
    standardized_contests_file_id = Column(
        String(200), ForeignKey("file.id", ondelete="set null")
    )
    standardized_contests_file = relationship(
        "File",
        foreign_keys=[standardized_contests_file_id],
        single_parent=True,
        cascade="all, delete-orphan",
    )
    standardized_contests = Column(JSON)

    __table_args__ = (UniqueConstraint("organization_id", "audit_name"),)


# these are typically counties
class Jurisdiction(BaseModel):
    id = Column(String(200), primary_key=True)
    election_id = Column(
        String(200), ForeignKey("election.id", ondelete="cascade"), nullable=False
    )
    election = relationship("Election", back_populates="jurisdictions")

    name = Column(String(200), nullable=False)

    # The ballot manifest file is uploaded by each jurisdiction to tell us
    # which ballots are available to audit.
    manifest_file_id = Column(String(200), ForeignKey("file.id", ondelete="set null"))
    manifest_file = relationship(
        "File",
        foreign_keys=[manifest_file_id],
        single_parent=True,
        cascade="all, delete-orphan",
    )
    manifest_num_ballots = Column(Integer)
    manifest_num_batches = Column(Integer)

    # The batch tallies file (only used in batch comparison audits), tells us
    # how many votes each contest choice got in a batch. We process it and
    # store it as a JSON blob in batch_tallies to be able to easily pass it
    # into the audit math for batch audits.
    batch_tallies_file_id = Column(
        String(200), ForeignKey("file.id", ondelete="set null")
    )
    batch_tallies_file = relationship(
        "File",
        foreign_keys=[batch_tallies_file_id],
        single_parent=True,
        cascade="all, delete-orphan",
    )
    batch_tallies = Column(JSON)

    # The CVR file (only used in ballot comparison audits), tells us all of the
    # recorded votes for each ballot in the election. We load this file and
    # create a CvrBallot for each row.
    cvr_file_id = Column(String(200), ForeignKey("file.id", ondelete="set null"))
    cvr_file = relationship(
        "File",
        foreign_keys=[cvr_file_id],
        single_parent=True,
        cascade="all, delete-orphan",
    )
    cvr_contests_metadata = Column(JSON)

    batches = relationship(
        "Batch", back_populates="jurisdiction", uselist=True, passive_deletes=True
    )
    audit_boards = relationship(
        "AuditBoard",
        back_populates="jurisdiction",
        uselist=True,
        passive_deletes=True,
        order_by="AuditBoard.name",
    )
    contests = relationship(
        "Contest",
        secondary="contest_jurisdiction",
        uselist=True,
        passive_deletes=True,
        order_by="Contest.created_at",
    )

    __table_args__ = (UniqueConstraint("election_id", "name"),)


class User(BaseModel):
    id = Column(String(200), primary_key=True)
    email = Column(String(200), unique=True, nullable=False)
    external_id = Column(String(200), unique=True)

    organizations = relationship(
        "Organization", secondary="audit_administration", uselist=True
    )
    jurisdictions = relationship(
        "Jurisdiction", secondary="jurisdiction_administration", uselist=True
    )

    @validates("email")
    def lowercase_email(self, _key, email):
        return email.lower()


class AuditAdministration(BaseModel):
    organization_id = Column(
        String(200), ForeignKey("organization.id", ondelete="cascade"), nullable=False,
    )
    user_id = Column(
        String(200), ForeignKey("user.id", ondelete="cascade"), nullable=False
    )

    organization = relationship(
        Organization,
        backref=backref("audit_administrations", cascade="all, delete-orphan"),
    )
    user = relationship(
        User, backref=backref("audit_administrations", cascade="all, delete-orphan")
    )

    __table_args__ = (PrimaryKeyConstraint("organization_id", "user_id"),)


class JurisdictionAdministration(BaseModel):
    user_id = Column(
        String(200), ForeignKey("user.id", ondelete="cascade"), nullable=False
    )
    jurisdiction_id = Column(
        String(200), ForeignKey("jurisdiction.id", ondelete="cascade"), nullable=False,
    )

    jurisdiction = relationship(
        Jurisdiction,
        backref=backref("jurisdiction_administrations", cascade="all, delete-orphan"),
    )
    user = relationship(
        User,
        backref=backref("jurisdiction_administrations", cascade="all, delete-orphan"),
    )

    __table_args__ = (PrimaryKeyConstraint("user_id", "jurisdiction_id"),)


# A batch represents a group of ballots in a jurisdiction (usually one physical
# box or bin).
class Batch(BaseModel):
    id = Column(String(200), primary_key=True)
    jurisdiction_id = Column(
        String(200), ForeignKey("jurisdiction.id", ondelete="cascade"), nullable=False,
    )
    jurisdiction = relationship("Jurisdiction", back_populates="batches")

    container = Column(String(200))
    tabulator = Column(String(200))
    name = Column(String(200), nullable=False)
    num_ballots = Column(Integer, nullable=False)

    # For ballot polling audits, a batch is associated with a group of ballots
    # sampled from this batch
    ballots = relationship(
        "SampledBallot", back_populates="batch", uselist=True, passive_deletes=True
    )

    # For batch comparison audits, we sample the batch itself, and assign it to
    # an audit board to be audited.
    audit_board_id = Column(
        String(200), ForeignKey("audit_board.id", ondelete="cascade"),
    )
    audit_board = relationship("AuditBoard")
    draws = relationship(
        "SampledBatchDraw",
        uselist=True,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    results = relationship(
        "BatchResult", uselist=True, cascade="all, delete-orphan", passive_deletes=True,
    )

    __table_args__ = (UniqueConstraint("jurisdiction_id", "tabulator", "name"),)


class Contest(BaseModel):
    id = Column(String(200), primary_key=True)
    election_id = Column(
        String(200), ForeignKey("election.id", ondelete="cascade"), nullable=False
    )
    election = relationship("Election", back_populates="contests")

    name = Column(String(200), nullable=False)
    # is_targeted = True for targeted contests, False for opportunistic contests
    is_targeted = Column(Boolean, nullable=False)

    total_ballots_cast = Column(Integer)
    num_winners = Column(Integer)
    votes_allowed = Column(Integer)

    choices = relationship(
        "ContestChoice",
        back_populates="contest",
        uselist=True,
        passive_deletes=True,
        order_by="ContestChoice.created_at",
    )
    jurisdictions = relationship(
        "Jurisdiction",
        secondary="contest_jurisdiction",
        uselist=True,
        order_by="Jurisdiction.name",
        passive_deletes=True,
    )
    results = relationship(
        "RoundContestResult",
        back_populates="contest",
        uselist=True,
        passive_deletes=True,
    )


class ContestChoice(BaseModel):
    id = Column(String(200), primary_key=True)
    contest_id = Column(
        String(200), ForeignKey("contest.id", ondelete="cascade"), nullable=False,
    )
    contest = relationship("Contest", back_populates="choices")

    name = Column(String(200), nullable=False)
    num_votes = Column(Integer, nullable=False)

    results = relationship(
        "RoundContestResult",
        back_populates="contest_choice",
        uselist=True,
        passive_deletes=True,
    )
    __table_args__ = (UniqueConstraint("id", "contest_id"),)


contest_jurisdiction = Table(
    "contest_jurisdiction",
    Base.metadata,
    Column(
        "contest_id",
        String(200),
        ForeignKey("contest.id", ondelete="cascade"),
        nullable=False,
    ),
    Column(
        "jurisdiction_id",
        String(200),
        ForeignKey("jurisdiction.id", ondelete="cascade"),
        nullable=False,
    ),
    PrimaryKeyConstraint("contest_id", "jurisdiction_id"),
)


class Affiliation(str, enum.Enum):
    DEMOCRAT = "DEM"
    REPUBLICAN = "REP"
    LIBERTARIAN = "LIB"
    INDEPENDENT = "IND"
    OTHER = "OTH"


class AuditBoard(BaseModel):
    id = Column(String(200), primary_key=True)

    jurisdiction_id = Column(
        String(200), ForeignKey("jurisdiction.id", ondelete="cascade"), nullable=False,
    )
    jurisdiction = relationship("Jurisdiction", back_populates="audit_boards")

    round_id = Column(String(200), ForeignKey("round.id", ondelete="cascade"))
    round = relationship("Round", back_populates="audit_boards")

    name = Column(String(200))
    member_1 = Column(String(200))
    member_1_affiliation = Column(Enum(Affiliation))
    member_2 = Column(String(200))
    member_2_affiliation = Column(Enum(Affiliation))
    passphrase = Column(String(1000), unique=True)
    signed_off_at = Column(DateTime)

    sampled_ballots = relationship(
        "SampledBallot",
        back_populates="audit_board",
        uselist=True,
        passive_deletes=True,
        order_by="SampledBallot.id",
    )

    __table_args__ = (UniqueConstraint("jurisdiction_id", "round_id", "name"),)


class Round(BaseModel):
    id = Column(String(200), primary_key=True)
    election_id = Column(
        String(200), ForeignKey("election.id", ondelete="cascade"), nullable=False
    )
    election = relationship("Election", back_populates="rounds")

    round_num = Column(Integer, nullable=False)
    ended_at = Column(DateTime)

    __table_args__ = (UniqueConstraint("election_id", "round_num"),)

    round_contests = relationship(
        "RoundContest", back_populates="round", uselist=True, passive_deletes=True
    )
    sampled_ballot_draws = relationship(
        "SampledBallotDraw", back_populates="round", uselist=True, passive_deletes=True
    )
    audit_boards = relationship(
        "AuditBoard", back_populates="round", uselist=True, passive_deletes=True
    )


class BallotStatus(str, enum.Enum):
    NOT_AUDITED = "NOT_AUDITED"
    AUDITED = "AUDITED"
    NOT_FOUND = "NOT_FOUND"


# Represents a physical ballot. A ballot only gets interpreted by an audit
# board once per audit.
class SampledBallot(BaseModel):
    id = Column(String(200), primary_key=True)

    batch_id = Column(
        String(200), ForeignKey("batch.id", ondelete="cascade"), nullable=False
    )
    batch = relationship("Batch", back_populates="ballots")

    # this ballot position should be 1-indexed
    ballot_position = Column(Integer, nullable=False)

    __table_args__ = (UniqueConstraint("batch_id", "ballot_position"),)

    draws = relationship(
        "SampledBallotDraw",
        back_populates="sampled_ballot",
        uselist=True,
        passive_deletes=True,
    )

    audit_board_id = Column(
        String(200), ForeignKey("audit_board.id", ondelete="cascade"),
    )
    audit_board = relationship("AuditBoard", back_populates="sampled_ballots")

    status = Column(Enum(BallotStatus), nullable=False)
    interpretations = relationship(
        "BallotInterpretation",
        uselist=True,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


# Represents one sampling of a ballot in a specific round. A ballot can get
# drawn multiple times per round, so a ticket number is assigned to identify
# each draw.
class SampledBallotDraw(BaseModel):
    ballot_id = Column(
        String(200),
        ForeignKey("sampled_ballot.id", ondelete="cascade"),
        nullable=False,
    )
    sampled_ballot = relationship("SampledBallot", back_populates="draws")

    round_id = Column(
        String(200), ForeignKey("round.id", ondelete="cascade"), nullable=False
    )
    round = relationship("Round", back_populates="sampled_ballot_draws")

    contest_id = Column(
        String(200), ForeignKey("contest.id", ondelete="cascade"), nullable=False
    )
    contest = relationship("Contest")

    ticket_number = Column(String(200), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint("ballot_id", "round_id", "contest_id", "ticket_number"),
    )


class Interpretation(str, enum.Enum):
    BLANK = "BLANK"
    CANT_AGREE = "CANT_AGREE"
    VOTE = "VOTE"


# Represents how the audit board interpreted the vote for a specific contest
# when they were auditing one ballot.
class BallotInterpretation(BaseModel):
    ballot_id = Column(
        String(200),
        ForeignKey("sampled_ballot.id", ondelete="cascade"),
        nullable=False,
    )
    contest_id = Column(
        String(200), ForeignKey("contest.id", ondelete="cascade"), nullable=False
    )

    __table_args__ = (PrimaryKeyConstraint("ballot_id", "contest_id"),)

    interpretation = Column(Enum(Interpretation), nullable=False)
    selected_choices = relationship(
        "ContestChoice", uselist=True, secondary="ballot_interpretation_contest_choice"
    )
    comment = Column(Text)

    # If the number of selected_choices is greater than Contest.votes_allowed,
    # then the voter overvoted. We cache a flag here so we don't have to
    # recompute this in different places.
    is_overvote = Column(Boolean, nullable=False)


# Represents the choices selected on the ballot (as interpreted by an audit board).
ballot_interpretation_contest_choice = Table(
    "ballot_interpretation_contest_choice",
    Base.metadata,
    Column("ballot_id", String(200), nullable=False),
    Column("contest_id", String(200), nullable=False),
    Column("contest_choice_id", String(200), nullable=False),
    ForeignKeyConstraint(
        ["ballot_id", "contest_id"],
        ["ballot_interpretation.ballot_id", "ballot_interpretation.contest_id"],
    ),
    ForeignKeyConstraint(
        ["contest_choice_id", "contest_id"],
        ["contest_choice.id", "contest_choice.contest_id"],
    ),
)


class RoundContest(BaseModel):
    round_id = Column(
        String(200), ForeignKey("round.id", ondelete="cascade"), nullable=False
    )
    round = relationship("Round", back_populates="round_contests")

    contest_id = Column(
        String(200), ForeignKey("contest.id", ondelete="cascade"), nullable=False,
    )
    contest = relationship("Contest")

    results = relationship("RoundContestResult", uselist=True, passive_deletes=True,)

    __table_args__ = (PrimaryKeyConstraint("round_id", "contest_id"),)

    end_p_value = Column(Float)
    is_complete = Column(Boolean)
    sample_size = Column(Integer)


class RoundContestResult(BaseModel):
    round_id = Column(
        String(200), ForeignKey("round.id", ondelete="cascade"), nullable=False
    )
    contest_id = Column(
        String(200), ForeignKey("contest.id", ondelete="cascade"), nullable=False,
    )
    contest = relationship("Contest", back_populates="results")
    __table_args__ = (
        PrimaryKeyConstraint("round_id", "contest_choice_id"),
        ForeignKeyConstraint(
            ["round_id", "contest_id"],
            ["round_contest.round_id", "round_contest.contest_id"],
            ondelete="cascade",
        ),
    )

    contest_choice_id = Column(
        String(200),
        ForeignKey("contest_choice.id", ondelete="cascade"),
        nullable=False,
    )
    contest_choice = relationship("ContestChoice", back_populates="results")

    result = Column(Integer, nullable=False)


class JurisdictionResult(BaseModel):
    round_id = Column(
        String(200), ForeignKey("round.id", ondelete="cascade"), nullable=False
    )
    contest_id = Column(
        String(200), ForeignKey("contest.id", ondelete="cascade"), nullable=False,
    )
    jurisdiction_id = Column(
        String(200), ForeignKey("jurisdiction.id", ondelete="cascade"), nullable=False,
    )
    contest_choice_id = Column(
        String(200),
        ForeignKey("contest_choice.id", ondelete="cascade"),
        nullable=False,
    )
    result = Column(Integer, nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint("round_id", "jurisdiction_id", "contest_choice_id"),
        ForeignKeyConstraint(
            ["contest_id", "jurisdiction_id"],
            ["contest_jurisdiction.contest_id", "contest_jurisdiction.jurisdiction_id"],
            ondelete="cascade",
        ),
    )


# In batch comparison audits, a SampledBatchDraw represents the sampling of a
# batch to be audited. Batches can get sampled multiple times per round, so
# they are given a ticket number to uniquely identify each draw.
class SampledBatchDraw(BaseModel):
    batch_id = Column(
        String(200), ForeignKey("batch.id", ondelete="cascade"), nullable=False,
    )
    batch = relationship("Batch")
    round_id = Column(
        String(200), ForeignKey("round.id", ondelete="cascade"), nullable=False
    )

    ticket_number = Column(String(200), nullable=False)

    __table_args__ = (PrimaryKeyConstraint("batch_id", "round_id", "ticket_number"),)


# Records the audited vote count for one sampled batch for one contest choice.
class BatchResult(BaseModel):
    batch_id = Column(
        String(200), ForeignKey("batch.id", ondelete="cascade"), nullable=False,
    )
    contest_choice_id = Column(
        String(200),
        ForeignKey("contest_choice.id", ondelete="cascade"),
        nullable=False,
    )

    result = Column(Integer, nullable=False)

    __table_args__ = (PrimaryKeyConstraint("batch_id", "contest_choice_id"),)


# Only used in ballot comparison audits, a CvrBallot stores one row from the
# cast-vote record (CVR) uploaded by a jurisdiction. We compare this record to
# the audit board's interpretation of the ballot.
class CvrBallot(Base):
    batch_id = Column(
        String(200), ForeignKey("batch.id", ondelete="cascade"), nullable=False,
    )
    batch = relationship("Batch")
    ballot_position = Column(Integer, nullable=False)
    imprinted_id = Column(String(200), nullable=False)
    # We store the raw string of 0s and 1s from the CVR row to make insertion
    # fast. We parse them when needed by the audit math using the contest
    # headers saved in Juridsiction.cvr_contests_metadata.
    interpretations = Column(Text, nullable=False)

    __table_args__ = (PrimaryKeyConstraint("batch_id", "ballot_position"),)


class File(BaseModel):
    id = Column(String(200), primary_key=True)
    name = Column(String(250), nullable=False)
    contents = Column(Text, nullable=False)
    uploaded_at = Column(DateTime, nullable=False)

    # Metadata for processing files in the background.
    processing_started_at = Column(DateTime)
    processing_completed_at = Column(DateTime)
    processing_error = Column(Text)


class ProcessingStatus(str, enum.Enum):
    READY_TO_PROCESS = "READY_TO_PROCESS"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    ERRORED = "ERRORED"


class USState(str, enum.Enum):
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


def get_or_404(model: Type[Base], primary_key: str):
    instance = model.query.get(primary_key)
    if instance:
        return instance
    raise NotFound(f"{model.__class__.__name__} {primary_key} not found")
