from extensions import db
from datetime import datetime

class Interview(db.Model):
    __tablename__ = 'interviews'
    
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.String(50), unique=True, nullable=False)
    role = db.Column(db.String(100))
    candidate_name = db.Column(db.String(100))
    duration = db.Column(db.Integer, default=10)
    answers = db.Column(db.Text)
    qa_history = db.Column(db.Text)
    report = db.Column(db.Text)
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            'id': self.id,
            'room_id': self.room_id,
            'role': self.role,
            'candidate_name': self.candidate_name,
            'duration': self.duration,
            'answers': self.answers,
            'qa_history': self.qa_history,
            'report': self.report,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None
        }

def init_db():
    # This is now handled by db.create_all() in app.py
    pass

def create_interview(room_id, role, candidate_name, duration=10):
    interview = Interview(
        room_id=room_id,
        role=role,
        candidate_name=candidate_name,
        duration=duration,
        status='active'
    )
    db.session.add(interview)
    db.session.commit()

def save_answers(room_id, answers):
    interview = Interview.query.filter_by(room_id=room_id).first()
    if interview:
        interview.answers = answers
        db.session.commit()

def save_report(room_id, report, qa_history=None):
    interview = Interview.query.filter_by(room_id=room_id).first()
    if interview:
        interview.report = report
        interview.qa_history = qa_history
        interview.status = 'completed'
        interview.ended_at = datetime.utcnow()
        db.session.commit()

def end_interview(room_id):
    interview = Interview.query.filter_by(room_id=room_id).first()
    if interview:
        interview.status = 'ended'
        interview.ended_at = datetime.utcnow()
        db.session.commit()

def get_interview(room_id):
    return Interview.query.filter_by(room_id=room_id).first()

def get_all_interviews():
    return Interview.query.order_by(Interview.created_at.desc()).all()

def get_interviews_by_ids(room_ids):
    if not room_ids:
        return []
    return Interview.query.filter(Interview.room_id.in_(room_ids)).all()