
from app import db

# there is usually only one of these
# State is in here
class Election(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    state = db.Column(db.String(100), nullable=False)
    election_date = db.Column(db.Date, nullable=True)
    election_type = db.Column(db.String(200), nullable=True)
    meeting_date = db.Column(db.Date, nullable=True)
    desired_risk_limit = db.Column(db.Integer, nullable=True)
    random_seed = db.Column(db.String(100), nullable=True)

# these are typically counties
class Jurisdiction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    manifest = db.Column(db.Text, nullable=True)
    manifest_uploaded_at = db.Column(db.DateTime(timezone=False), nullable=True)
    cvrs = db.Column(db.Text, nullable=True)
    cvrs_uploaded_at = db.Column(db.DateTime(timezone=False), nullable=True)

# users that log in
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    election_id = db.Column(db.Integer, db.ForeignKey('election.id'), nullable=False)
    jurisdiction_id = db.Column(db.Integer, db.ForeignKey('jurisdiction.id'),
                                nullable=True)    

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

class JurisdictionRound(db.Model):
    jurisdiction_id = db.Column(db.Integer, db.ForeignKey('jurisdiction.id'), nullable=False)
    round_id = db.Column(db.Integer, db.ForeignKey('round.id'), nullable=False)

    __table_args__ = (
        db.PrimaryKeyConstraint('jurisdiction_id', 'round_id'),
    )

    num_ballots_to_audit = db.Column(db.Integer, nullable=True)

class CVR(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jurisdiction_id = db.Column(db.Integer, db.ForeignKey('jurisdiction.id'), nullable=False)
    round_id = db.Column(db.Integer, db.ForeignKey('round.id'), nullable=False)

class CVRSelection(db.Model):
    cvr_id = db.Column(db.Integer, db.ForeignKey('CVR.id'), nullable=False)
    contest_id = db.Column(db.Integer, db.ForeignKey('targeted_contest.id'), nullable=False)
    __table_args__ = (
        db.PrimaryKeyConstraint('cvr_id', 'contest_id'),
    )
    choice_id = db.Column(db.Integer, db.ForeignKey('targeted_contest_choice.id'), nullable=False)
