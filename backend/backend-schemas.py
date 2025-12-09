# backend/schemas.py
# Pydantic Request/Response Schemas

from pydantic import BaseModel
from typing import List, Optional

# ===== Interview Setup =====
class InterviewSetupRequest(BaseModel):
    job_description: str
    candidate_name: str
    duration_minutes: int = 5
    avatar_image_url: Optional[str] = None

class InterviewSetupResponse(BaseModel):
    session_id: str
    ws_url: str
    message: str

# ===== Evaluation =====
class EvaluationResult(BaseModel):
    score: float
    marks: str
    correctness: str
    relatedness: float
    depth: str
    next_question_type: str
    feedback: str
    confidence: float

# ===== WebSocket Messages =====
class AudioChunkMessage(BaseModel):
    type: str = "audio_chunk"
    data: str  # base64 encoded

class TranscriptionMessage(BaseModel):
    type: str = "transcription_partial"
    text: str

class EvaluationMessage(BaseModel):
    type: str = "evaluation"
    score: float
    marks: str
    feedback: str

class ResultsMessage(BaseModel):
    type: str = "results"
    overall_score: float
    recommendation: str
    breakdown: List[dict]
    strengths: List[str]
    weaknesses: List[str]

# ===== Interview Results =====
class BreakdownItem(BaseModel):
    question: str
    score: float
    marks: str
    feedback: str

class InterviewResults(BaseModel):
    overall_score: float
    recommendation: str
    breakdown: List[BreakdownItem]
    strengths: List[str]
    weaknesses: List[str]
