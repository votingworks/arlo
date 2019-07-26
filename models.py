
from app import db
from sqlalchemy.orm import relationship

# there is usually only one of these
# State is in here
class Election(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=True)
    state = db.Column(db.String(100), nullable=True)
    election_date = db.Column(db.Date, nullable=True)
    election_type = db.Column(db.String(200), nullable=True)
    meeting_date = db.Column(db.Date, nullable=True)
    risk_limit = db.Column(db.Integer, nullable=True)
    random_seed = db.Column(db.String(100), nullable=True)
    sample_size_options = db.Column(db.String(1000), nullable=True)
    jurisdictions = relationship('Jurisdiction', back_populates='election')
    contests = relationship('TargetedContest', back_populates='election')
    rounds = relationship('Round', back_populates='election')
    

# these are typically counties
class Jurisdiction(db.Model):
    id = db.Column(db.String(200), primary_key=True)
    election_id = db.Column(db.Integer, db.ForeignKey('election.id', ondelete='cascade'), nullable=False)
    election = relationship('Election', back_populates = 'jurisdictions')
    batches = relationship('Batch', back_populates='jurisdiction')
    name = db.Column(db.String(200), unique=True, nullable=False)

    manifest = db.Column(db.Text, nullable=True)
    manifest_filename = db.Column(db.String(250), nullable=True)
    manifest_uploaded_at = db.Column(db.DateTime(timezone=False), nullable=True)
    manifest_num_ballots = db.Column(db.Integer)
    manifest_num_batches = db.Column(db.Integer)

    # any error in the upload? null == none
    manifest_errors = db.Column(db.Text, nullable=True)

    # a JSON array of field names that are included in the CSV
    manifest_fields = db.Column(db.Text, nullable=True)

    audit_boards = relationship('AuditBoard', back_populates='jurisdiction')
    contests = relationship('TargetedContestJurisdiction', back_populates='jurisdiction')

# users that log in
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    election_id = db.Column(db.Integer, db.ForeignKey('election.id', ondelete='cascade'), nullable=False)
    jurisdiction_id = db.Column(db.String(200), db.ForeignKey('jurisdiction.id'),
                                nullable=True)    

class Batch(db.Model):
    id = db.Column(db.String(200), primary_key=True)
    jurisdiction_id = db.Column(db.String(200), db.ForeignKey('jurisdiction.id', ondelete='cascade'), nullable=False)
    jurisdiction = relationship('Jurisdiction', back_populates='batches')
    name = db.Column(db.String(200), nullable=False)
    num_ballots = db.Column(db.Integer, nullable=False)

    storage_location = db.Column(db.String(200), nullable=True)
    tabulator = db.Column(db.String(200), nullable=True)
        
class TargetedContest(db.Model):
    id = db.Column(db.String(200), primary_key=True)
    election_id = db.Column(db.Integer, db.ForeignKey('election.id', ondelete='cascade'), nullable=False)
    election = relationship('Election', back_populates = 'contests')
    choices = relationship('TargetedContestChoice', back_populates='contest')
    name = db.Column(db.String(200), nullable=False)
    total_ballots_cast = db.Column(db.Integer, nullable=False)

class TargetedContestChoice(db.Model):
    id = db.Column(db.String(200), primary_key=True)
    contest_id = db.Column(db.String(200), db.ForeignKey('targeted_contest.id', ondelete='cascade'), nullable=False)
    contest = relationship('TargetedContest', back_populates='choices')    
    name = db.Column(db.String(200), nullable=False)
    num_votes = db.Column(db.Integer, nullable=False)

    results = relationship('RoundContestResult', back_populates='targeted_contest_choice')

class TargetedContestJurisdiction(db.Model):
    contest_id = db.Column(db.String(200), db.ForeignKey('targeted_contest.id', ondelete='cascade'), nullable=False)
    jurisdiction = relationship('Jurisdiction', back_populates= 'contests')
    jurisdiction_id = db.Column(db.String(200), db.ForeignKey('jurisdiction.id', ondelete='cascade'), nullable=False)

    __table_args__ = (
        db.PrimaryKeyConstraint('contest_id', 'jurisdiction_id'),
    )

class AuditBoard(db.Model):
    id = db.Column(db.String(200), primary_key=True)
    jurisdiction_id = db.Column(db.String(200), db.ForeignKey('jurisdiction.id', ondelete='cascade'), nullable=False)
    jurisdiction = relationship(Jurisdiction, back_populates='audit_boards')
    
    member_1 = db.Column(db.String(200), nullable=True)
    member_1_affiliation = db.Column(db.String(200), nullable=True)
    member_2 = db.Column(db.String(200), nullable=True)
    member_2_affiliation = db.Column(db.String(200), nullable=True)
    
class Round(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    election_id = db.Column(db.Integer, db.ForeignKey('election.id', ondelete='cascade'), nullable=False)
    election = relationship('Election', back_populates = 'rounds')
    started_at = db.Column(db.DateTime, nullable=False)
    ended_at = db.Column(db.DateTime, nullable=True)
    round_contests = relationship('RoundContest', back_populates='round')

class SampledBallot(db.Model):
    round_id = db.Column(db.Integer, db.ForeignKey('round.id'), nullable=False)
    jurisdiction_id = db.Column(db.String(200), db.ForeignKey('jurisdiction.id', ondelete='cascade'), nullable=False)

    batch_id = db.Column(db.String(200), db.ForeignKey('batch.id'), nullable=False)
    batch = relationship('Batch')
    
    ballot_position = db.Column(db.Integer, nullable=False)
    
    __table_args__ = (
        db.PrimaryKeyConstraint('round_id', 'jurisdiction_id', 'batch_id', 'ballot_position'),
    )
    
    times_sampled = db.Column(db.Integer, nullable=False)
    audit_board_id = db.Column(db.String(200), db.ForeignKey('audit_board.id'), nullable=False)    
    
class RoundContest(db.Model):
    round_id = db.Column(db.Integer, db.ForeignKey('round.id', ondelete='cascade'), nullable=False)
    contest_id = db.Column(db.String(200), db.ForeignKey('targeted_contest.id', ondelete='cascade'), nullable=False)
    round = relationship('Round', back_populates='round_contests')
    results = relationship('RoundContestResult')

    __table_args__ = (
        db.PrimaryKeyConstraint('round_id', 'contest_id'),
    )

    end_p_value = db.Column(db.Float)
    is_complete = db.Column(db.Boolean)

    sample_size = db.Column(db.Integer)

class RoundContestResult(db.Model):
    round_id = db.Column(db.Integer, db.ForeignKey('round.id', ondelete='cascade'), nullable=False)
    contest_id = db.Column(db.String(200), db.ForeignKey('targeted_contest.id', ondelete='cascade'), nullable=False)
    contest = relationship('TargetedContest', viewonly=True)
    round_contest = relationship('RoundContest', foreign_keys=[round_id, contest_id], back_populates = 'results')
    targeted_contest_choice_id = db.Column(db.String(200), db.ForeignKey('targeted_contest_choice.id', ondelete='cascade'), nullable=False)
    targeted_contest_choice = relationship('TargetedContestChoice')

    __table_args__ = (
        db.PrimaryKeyConstraint('round_id', 'targeted_contest_choice_id'),
        db.ForeignKeyConstraint(['round_id', 'contest_id'], ['round_contest.round_id', 'round_contest.contest_id'])
    )

    result = db.Column(db.Integer)
   
