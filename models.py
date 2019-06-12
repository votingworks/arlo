
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
    desired_risk_limit = db.Column(db.Integer, nullable=True)
    random_seed = db.Column(db.String(100), nullable=True)
    jurisdictions = relationship('Jurisdiction', back_populates='election')

# these are typically counties
class Jurisdiction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    election_id = db.Column(db.Integer, db.ForeignKey('election.id'), nullable=False)
    election = relationship('Election', back_populates = 'jurisdictions')
    name = db.Column(db.String(200), unique=True, nullable=False)
    manifest = db.Column(db.Text, nullable=True)
    manifest_uploaded_at = db.Column(db.DateTime(timezone=False), nullable=True)

    # any error in the upload? null == none
    manifest_errors = db.Column(db.Text, nullable=True)

    # a JSON array of field names that are included in the CSV
    manifest_fields = db.Column(db.Text, nullable=True)

    cvrs = db.Column(db.Text, nullable=True)
    cvrs_uploaded_at = db.Column(db.DateTime(timezone=False), nullable=True)

# users that log in
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    election_id = db.Column(db.Integer, db.ForeignKey('election.id'), nullable=False)
    jurisdiction_id = db.Column(db.Integer, db.ForeignKey('jurisdiction.id'),
                                nullable=True)    

class Batch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jurisdiction_id = db.Column(db.Integer, db.ForeignKey('jurisdiction.id'), nullable=False)
    num_ballots = db.Column(db.Integer, nullable=False)

    # JSON dictionary of all the field values that correspond to manifest_fields
    field_values = db.Column(db.Text, nullable=False)
        
class TargetedContest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    ballots_cast = db.Column(db.Integer, nullable=False)

class TargetedContestChoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    contest_id = db.Column(db.Integer, db.ForeignKey('targeted_contest.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    num_votes_for = db.Column(db.Integer, nullable=False)

class TargetedContestJurisdiction(db.Model):
    contest_id = db.Column(db.Integer, db.ForeignKey('targeted_contest.id'), nullable=False)
    jurisdiction_id = db.Column(db.Integer, db.ForeignKey('jurisdiction.id'), nullable=False)

    __table_args__ = (
        db.PrimaryKeyConstraint('contest_id', 'jurisdiction_id'),
    )

class AuditBoard(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jurisdiction_id = db.Column(db.Integer, db.ForeignKey('jurisdiction.id'), nullable=False)
    member_1 = db.Column(db.String(200), nullable=True)
    member_1_affiliation = db.Column(db.String(200), nullable=True)
    member_2 = db.Column(db.String(200), nullable=True)
    member_2_affiliation = db.Column(db.String(200), nullable=True)
    
class Round(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    started_at = db.Column(db.DateTime, nullable=False)
    ended_at = db.Column(db.DateTime, nullable=True)

class CVR(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jurisdiction_id = db.Column(db.Integer, db.ForeignKey('jurisdiction.id'), nullable=False)
    round_id = db.Column(db.Integer, db.ForeignKey('round.id'), nullable=False)
    audit_board_id = db.Column(db.Integer, db.ForeignKey('audit_board.id'), nullable=False)
    batch_id = db.Column(db.Integer, db.ForeignKey('batch.id'), nullable=False)
    position = db.Column(db.Integer, nullable=False)
    
    audited_at = db.Column(db.DateTime, nullable=True)
    marked_not_found_at = db.Column(db.DateTime, nullable=True)

class CVRSelection(db.Model):
    cvr_id = db.Column(db.Integer, db.ForeignKey('CVR.id'), nullable=False)
    contest_id = db.Column(db.Integer, db.ForeignKey('targeted_contest.id'), nullable=False)
    __table_args__ = (
        db.PrimaryKeyConstraint('cvr_id', 'contest_id'),
    )

    # choice can be null if ballot is blank
    choice_id = db.Column(db.Integer, db.ForeignKey('targeted_contest_choice.id'), nullable=True)

    # consensus should be False if there is no audit board consensus
    consensus = db.Column(db.Boolean, nullable=False)

    comment = db.Column(db.String(250), nullable=True)
    
