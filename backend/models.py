# backend/models.py
# SQLAlchemy ORM Models (Placeholder for database)

import os
from datetime import datetime

def db_init():
    """Initialize database"""
    # In production, use SQLAlchemy with SQLite
    # For now, just ensure data directory exists
    os.makedirs("data", exist_ok=True)
    print("Database initialized")

class User:
    """User model"""
    def __init__(self, id, email, name):
        self.id = id
        self.email = email
        self.name = name
        self.created_at = datetime.now()

class Interview:
    """Interview session model"""
    def __init__(self, session_id, job_description, candidate_name, duration_minutes):
        self.session_id = session_id
        self.job_description = job_description
        self.candidate_name = candidate_name
        self.interview_duration_minutes = duration_minutes
        self.status = "setup"
        self.start_time = datetime.now()
        self.end_time = None
        self.overall_score = None
        self.recommendation = None
        self.created_at = datetime.now()

class InterviewQuestion:
    """Question in interview"""
    def __init__(self, interview_id, question_index, text):
        self.interview_id = interview_id
        self.question_index = question_index
        self.question_text = text
        self.created_at = datetime.now()

class CandidateResponse:
    """Candidate's response to a question"""
    def __init__(self, interview_id, question_id, text):
        self.interview_id = interview_id
        self.question_id = question_id
        self.response_text = text
        self.created_at = datetime.now()

class QuestionEvaluation:
    """Evaluation of a response"""
    def __init__(self, interview_id, question_id, score, feedback):
        self.interview_id = interview_id
        self.question_id = question_id
        self.score = score
        self.feedback = feedback
        self.created_at = datetime.now()

class InterviewResult:
    """Final results of an interview"""
    def __init__(self, interview_id, overall_score, recommendation):
        self.interview_id = interview_id
        self.overall_score = overall_score
        self.recommendation = recommendation
        self.created_at = datetime.now()
