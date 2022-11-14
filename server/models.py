import enum
from typing import Type
from datetime import datetime as dt, timezone
from werkzeug.exceptions import NotFound
import sqlalchemy
from sqlalchemy import (
    Table,
    DDL,
    DateTime,
    Column,
    String,
    Text,
    Integer,
    Float,
    JSON,
    Boolean,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    UniqueConstraint,
    PrimaryKeyConstraint,
    CheckConstraint,
)
from sqlalchemy.orm import relationship, backref, validates
from sqlalchemy.types import TypeDecorator
from sqlalchemy.dialects import postgresql
from .database import Base  # pylint: disable=cyclic-import

# Define a custom function to sort mixed text/number strings
# From https://stackoverflow.com/a/20667107/1472662
# You can call this function using func.human_sort
sqlalchemy.event.listen(
    Base.metadata,
    "after_create",
    DDL(
        """
BEGIN;
SELECT pg_advisory_xact_lock(2142616474639426746); -- lock so that tests can run this concurrently
CREATE OR REPLACE FUNCTION human_sort(text)
  RETURNS text[] AS
$BODY$
  /* Split the input text into contiguous chunks where no numbers appear,
     and contiguous chunks of only numbers. For the numbers, add leading
     zeros to 20 digits, so we can use one text array, but sort the
     numbers as if they were big integers.

       For example, human_sort('Run 12 Miles') gives
            {'Run ', '00000000000000000012', ' Miles'}
  */
  select array_agg(
    case
      when a.match_array[1]::text is not null
        then a.match_array[1]::text
      else lpad(a.match_array[2]::text, 20::int, '0'::text)::text
    end::text)
    from (
      select regexp_matches(
        case when $1 = '' then null else $1 end, E'(\\\\D+)|(\\\\d+)', 'g'
      ) AS match_array
    ) AS a
$BODY$
  LANGUAGE sql IMMUTABLE;
COMMIT;
"""
    ),
)


class UTCDateTime(TypeDecorator):  # pylint: disable=abstract-method
    # Store with no timezone
    impl = DateTime

    # Ensure UTC timezone on write
    def process_bind_param(self, value, dialect):
        if value:
            assert (
                value.tzinfo == timezone.utc
            ), "All datetimes must have UTC timezone - use datetime.now(timezone.utc)"
        return value

    # Repopulate UTC timezone on read
    def process_result_value(self, value, dialect):
        return value and value.replace(tzinfo=timezone.utc)


class BaseModel(Base):
    __abstract__ = True
    created_at = Column(
        UTCDateTime, default=lambda: dt.now(timezone.utc), nullable=False
    )
    updated_at = Column(
        UTCDateTime,
        default=lambda: dt.now(timezone.utc),
        onupdate=lambda: dt.now(timezone.utc),
        nullable=False,
    )


# on-delete-cascade is done in SQLAlchemy like this:
# https://stackoverflow.com/questions/5033547/sqlalchemy-cascade-delete


class Organization(BaseModel):
    id = Column(String(200), primary_key=True)
    name = Column(String(200), nullable=False, unique=True)

    elections = relationship(
        "Election",
        back_populates="organization",
        cascade="all, delete",
        passive_deletes=True,
        order_by="Election.audit_name",
    )


class AuditType(str, enum.Enum):
    BALLOT_POLLING = "BALLOT_POLLING"
    BATCH_COMPARISON = "BATCH_COMPARISON"
    BALLOT_COMPARISON = "BALLOT_COMPARISON"
    HYBRID = "HYBRID"


class AuditMathType(str, enum.Enum):
    BRAVO = "BRAVO"
    MINERVA = "MINERVA"
    SUPERSIMPLE = "SUPERSIMPLE"
    MACRO = "MACRO"
    SUITE = "SUITE"


# Election is a slight misnomer - this model represents an audit.
class Election(BaseModel):
    id = Column(String(200), primary_key=True)
    # audit_name must be unique within each Organization
    audit_name = Column(String(200), nullable=False)
    audit_type = Column(Enum(AuditType), nullable=False)
    audit_math_type = Column(Enum(AuditMathType), nullable=False)
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
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Jurisdiction.name",
    )
    contests = relationship(
        "Contest",
        back_populates="election",
        uselist=True,
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Contest.created_at",
    )
    rounds = relationship(
        "Round",
        back_populates="election",
        uselist=True,
        cascade="all, delete-orphan",
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

    # When a user deletes an audit, we keep it in the database just in case
    # they change their mind, but flag it so that we can restrict access
    deleted_at = Column(UTCDateTime)

    __table_args__ = (UniqueConstraint("organization_id", "audit_name"),)


class CvrFileType(str, enum.Enum):
    DOMINION = "DOMINION"
    CLEARBALLOT = "CLEARBALLOT"
    ESS = "ESS"
    HART = "HART"


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
    cvr_file_type = Column(Enum(CvrFileType))
    cvr_contests_metadata = Column(JSON)

    # Sometimes contest names in a jurisdiction's CVR don't match the contest
    # names selected by the AA. Here we store corrections made by the AA to
    # apply to the cvr_contests_metadata.
    # { contest_name: cvr_contest_name }
    contest_name_standardizations = Column(JSON)

    finalized_full_hand_tally_results_at = Column(UTCDateTime)

    # In batch comparison audits, JMs can generate a login link for additional
    # tally entry users to log in.
    tally_entry_passphrase = Column(String(200))

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
        "Organization",
        secondary="audit_administration",
        uselist=True,
        order_by="Organization.name",
    )
    jurisdictions = relationship(
        "Jurisdiction", secondary="jurisdiction_administration", uselist=True
    )

    # Jurisdiction admins log in by requesting a one-time code.
    login_code = Column(String(200))
    login_code_requested_at = Column(UTCDateTime)
    login_code_attempts = Column(Integer)

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

    # For ballot polling and ballot comparison audits, a batch is associated
    # with a group of ballots sampled from this batch
    ballots = relationship(
        "SampledBallot", back_populates="batch", uselist=True, passive_deletes=True
    )

    # For hybrid audits, the ballot manifest tells us which batches have CVRs
    # (and should use ballot comparison math) and which don't (and should use
    # ballot polling math).
    has_cvrs = Column(Boolean)

    draws = relationship(
        "SampledBatchDraw",
        uselist=True,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    result_tally_sheets = relationship(
        "BatchResultTallySheet",
        uselist=True,
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="BatchResultTallySheet.created_at",
    )

    # Only one of the following should be populated, enforced via a check constraint defined below
    last_edited_by_support_user_email = Column(String(200))
    last_edited_by_user_id = Column(String(200), ForeignKey("user.id"))
    last_edited_by_tally_entry_user_id = Column(
        String(200), ForeignKey("tally_entry_user.id")
    )

    last_edited_by_user = relationship("User")
    last_edited_by_tally_entry_user = relationship("TallyEntryUser")

    __table_args__ = (
        UniqueConstraint("jurisdiction_id", "tabulator", "name"),
        CheckConstraint(
            "(cast(last_edited_by_support_user_email is not null as int) +"
            " cast(last_edited_by_user_id is not null as int) +"
            " cast(last_edited_by_tally_entry_user_id is not null as int)) <= 1",
            "only_one_of_last_edited_by_fields_is_specified_check",
        ),
    )


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
        cascade="all, delete-orphan",
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


# In ballot polling/comparison audits, ballots are divvied up between audit
# boards, who can log in and enter their ballot interpretation
class AuditBoard(BaseModel):
    id = Column(String(200), primary_key=True)

    jurisdiction_id = Column(
        String(200), ForeignKey("jurisdiction.id", ondelete="cascade"), nullable=False,
    )
    jurisdiction = relationship("Jurisdiction", back_populates="audit_boards")

    round_id = Column(
        String(200), ForeignKey("round.id", ondelete="cascade"), nullable=False
    )
    round = relationship("Round", back_populates="audit_boards")

    name = Column(String(200))
    member_1 = Column(String(200))
    member_1_affiliation = Column(Enum(Affiliation))
    member_2 = Column(String(200))
    member_2_affiliation = Column(Enum(Affiliation))
    passphrase = Column(String(1000), unique=True)
    signed_off_at = Column(UTCDateTime)

    sampled_ballots = relationship(
        "SampledBallot",
        back_populates="audit_board",
        uselist=True,
        passive_deletes=True,
        order_by="SampledBallot.id",
    )

    __table_args__ = (UniqueConstraint("jurisdiction_id", "round_id", "name"),)


# In batch comparison audits, jurisdiction managers can allow additional people
# to log in and help enter tallies using a TallyEntryUser
class TallyEntryUser(BaseModel):
    id = Column(String(200), primary_key=True)

    jurisdiction_id = Column(
        String(200), ForeignKey("jurisdiction.id", ondelete="cascade"), nullable=False,
    )
    jurisdiction = relationship("Jurisdiction")

    # In some cases, the tally entry user might be an audit board and have
    # multiple members. In others, it might just be one person.
    member_1 = Column(String(200))
    member_1_affiliation = Column(Enum(Affiliation))
    member_2 = Column(String(200))
    member_2_affiliation = Column(Enum(Affiliation))

    login_code = Column(String(200))
    login_confirmed_at = Column(UTCDateTime)

    __table_args__ = (UniqueConstraint("jurisdiction_id", "login_code"),)


class SampleSizeOptions(BaseModel):
    election_id = Column(
        String(200), ForeignKey("election.id", ondelete="cascade"), nullable=False
    )
    round_num = Column(Integer, nullable=False)

    task_id = Column(String(200), ForeignKey("background_task.id", ondelete="set null"))
    task = relationship(
        "BackgroundTask", single_parent=True, cascade="all, delete-orphan"
    )
    sample_size_options = Column(JSON)

    __table_args__ = (PrimaryKeyConstraint("election_id", "round_num"),)


class Round(BaseModel):
    id = Column(String(200), primary_key=True)
    election_id = Column(
        String(200), ForeignKey("election.id", ondelete="cascade"), nullable=False
    )
    election = relationship("Election", back_populates="rounds")

    round_num = Column(Integer, nullable=False)
    ended_at = Column(UTCDateTime)

    draw_sample_task_id = Column(
        String(200), ForeignKey("background_task.id", ondelete="set null")
    )
    draw_sample_task = relationship("BackgroundTask")

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
        String(200), ForeignKey("audit_board.id", ondelete="set null")
    )
    audit_board = relationship("AuditBoard", back_populates="sampled_ballots")

    status = Column(Enum(BallotStatus), nullable=False)
    interpretations = relationship(
        "BallotInterpretation",
        uselist=True,
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="BallotInterpretation.created_at",
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
    CONTEST_NOT_ON_BALLOT = "CONTEST_NOT_ON_BALLOT"
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
        "ContestChoice",
        uselist=True,
        secondary="ballot_interpretation_contest_choice",
        primaryjoin="and_("
        + "ballot_interpretation.c.ballot_id == ballot_interpretation_contest_choice.c.ballot_id,"
        + "ballot_interpretation.c.contest_id == ballot_interpretation_contest_choice.c.contest_id)",
        order_by="ContestChoice.created_at",
    )
    comment = Column(Text)

    # If the number of selected_choices is greater than Contest.votes_allowed,
    # then the voter overvoted. We cache a flag here so we don't have to
    # recompute this in different places.
    is_overvote = Column(Boolean, nullable=False)

    # If a ballot has an invalid write-in with no other selections, the corresponding interpretation
    # will be BLANK. If a ballot for a vote-for-n contest has an invalid write-in alongside a valid
    # selection, the corresponding interpretation will be VOTE.
    has_invalid_write_in = Column(Boolean, nullable=False)


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
        ondelete="cascade",
    ),
    ForeignKeyConstraint(
        ["contest_choice_id", "contest_id"],
        ["contest_choice.id", "contest_choice.contest_id"],
        ondelete="cascade",
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

    results = relationship(
        "RoundContestResult",
        uselist=True,
        passive_deletes=True,
        cascade="all, delete-orphan",
    )

    __table_args__ = (PrimaryKeyConstraint("round_id", "contest_id"),)

    end_p_value = Column(Float)
    is_complete = Column(Boolean)
    sample_size = Column(JSON)


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


# In a full hand tally, records the audited vote count for one
# batch for one contest choice. Note that we don't require the batch name to
# match any of the batches in the ballot manifest.
class FullHandTallyBatchResult(BaseModel):
    jurisdiction_id = Column(
        String(200), ForeignKey("jurisdiction.id", ondelete="cascade"), nullable=False,
    )
    batch_name = Column(String(200), nullable=False)
    batch_type = Column(String(200), nullable=False)
    contest_choice_id = Column(
        String(200),
        ForeignKey("contest_choice.id", ondelete="cascade"),
        nullable=False,
    )

    result = Column(Integer, nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint("jurisdiction_id", "batch_name", "contest_choice_id"),
    )


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


# (Experimental) To we add extra batches on top of the sample, give them a
# special ticket number to flag them.
EXTRA_TICKET_NUMBER = "EXTRA"

# In a batch comparison audit, audit boards will record votes on tally sheets.
# They may use one sheet for the whole batch, or split the batch up and use
# multiple sheets.
class BatchResultTallySheet(BaseModel):
    id = Column(String(200), primary_key=True)
    batch_id = Column(
        String(200), ForeignKey("batch.id", ondelete="cascade"), nullable=False,
    )
    name = Column(String(200), nullable=False)

    results = relationship(
        "BatchResult", uselist=True, cascade="all, delete-orphan", passive_deletes=True,
    )

    __table_args__ = (UniqueConstraint("batch_id", "name"),)


# Each tally sheet has an audited vote count (BatchResult) for each contest
# choice.
class BatchResult(BaseModel):
    tally_sheet_id = Column(
        String(200),
        ForeignKey("batch_result_tally_sheet.id", ondelete="cascade"),
        nullable=False,
    )
    contest_choice_id = Column(
        String(200),
        ForeignKey("contest_choice.id", ondelete="cascade"),
        nullable=False,
    )

    result = Column(Integer, nullable=False)

    __table_args__ = (PrimaryKeyConstraint("tally_sheet_id", "contest_choice_id"),)


# Records when the jurisdiction finalizes their batch results for a round.
class BatchResultsFinalized(BaseModel):
    jurisdiction_id = Column(
        String(200), ForeignKey("jurisdiction.id", ondelete="cascade"), nullable=False,
    )
    round_id = Column(
        String(200), ForeignKey("round.id", ondelete="cascade"), nullable=False
    )
    __table_args__ = (PrimaryKeyConstraint("jurisdiction_id", "round_id"),)


# Only used in ballot comparison audits, a CvrBallot stores one row from the
# cast-vote record (CVR) uploaded by a jurisdiction. We compare this record to
# the audit board's interpretation of the ballot.
class CvrBallot(Base):
    batch_id = Column(
        String(200), ForeignKey("batch.id", ondelete="cascade"), nullable=False,
    )
    batch = relationship("Batch")
    # record_id is the identifying number given to the ballot by the tabulator
    # (it uniquely identifies ballots in a batch within the CVR)
    record_id = Column(Integer, nullable=False)
    # ballot_position is the counting index of the ballot among all ballots
    # from the batch in the CVR - we use this to match with sampled ballots from the manifest
    ballot_position = Column(Integer)
    # imprinted_id is a field in the CVR that uniquely identifies the ballot
    imprinted_id = Column(String(200), nullable=False)
    # We store the raw string of 0s and 1s from the CVR row to make insertion
    # fast. We parse them when needed by the audit math using the contest
    # headers saved in Juridsiction.cvr_contests_metadata.
    interpretations = Column(Text, nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint("batch_id", "record_id"),
        UniqueConstraint("batch_id", "ballot_position"),
    )


class File(BaseModel):
    id = Column(String(200), primary_key=True)
    name = Column(String(250), nullable=False)
    storage_path = Column(String(250), nullable=False)
    uploaded_at = Column(UTCDateTime, nullable=False)

    task_id = Column(String(200), ForeignKey("background_task.id"))
    task = relationship("BackgroundTask")


class BackgroundTask(BaseModel):
    id = Column(String(200), primary_key=True)
    task_name = Column(String(200), nullable=False)
    payload = Column(JSON, nullable=False)

    started_at = Column(UTCDateTime)
    completed_at = Column(UTCDateTime)
    error = Column(Text)

    # Tasks can record progress in the work unit of their choosing
    work_total = Column(Integer)
    work_progress = Column(Integer)


class ActivityLogRecord(Base):
    id = Column(String(200), primary_key=True)
    timestamp = Column(UTCDateTime, nullable=False)
    organization_id = Column(
        String(200), ForeignKey("organization.id", ondelete="cascade"), nullable=False
    )
    activity_name = Column(String(200), nullable=False)
    info = Column(postgresql.JSON, nullable=False)

    posted_to_slack_at = Column(UTCDateTime)


class BatchInventoryData(BaseModel):
    jurisdiction_id = Column(
        String(200),
        ForeignKey("jurisdiction.id", ondelete="cascade"),
        nullable=False,
        primary_key=True,
    )

    cvr_file_id = Column(String(200), ForeignKey("file.id", ondelete="set null"))
    cvr_file = relationship(
        "File",
        foreign_keys=[cvr_file_id],
        single_parent=True,
        cascade="all, delete-orphan",
    )
    tabulator_status_file_id = Column(
        String(200), ForeignKey("file.id", ondelete="set null")
    )
    tabulator_status_file = relationship(
        "File",
        foreign_keys=[tabulator_status_file_id],
        single_parent=True,
        cascade="all, delete-orphan",
    )

    election_results = Column(JSON)
    tabulator_id_to_name = Column(JSON)

    sign_off_user_id = Column(String(200), ForeignKey("user.id", ondelete="set null"))
    signed_off_at = Column(UTCDateTime)


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
