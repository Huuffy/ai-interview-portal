# backend/utils.py
# Helper Functions, Validators, Constants

import logging
from typing import Dict, Any

# ===== LOGGER =====
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ===== SCORING FUNCTIONS =====
def calculate_score(relatedness: float, correctness: Dict, depth: Dict, confidence: float = 0.85) -> float:
    """
    Calculate final score (0-10) based on:
    - Relatedness (0-1): Does response relate to question?
    - Correctness (good/partial/poor): Is answer correct?
    - Depth (shallow/medium/deep): How detailed?
    - Confidence (0-1): How confident in evaluation?
    """
    # Base score from relatedness (0-5)
    relatedness_score = relatedness * 5
    
    # Correctness adjustment (0-3)
    assessment = correctness.get("assessment", "partial").lower()
    if assessment == "good":
        correctness_score = 3
    elif assessment == "partial":
        correctness_score = 1.5
    else:
        correctness_score = 0
    
    # Depth adjustment (0-2)
    depth_level = depth.get("level", "medium").lower()
    if depth_level == "deep":
        depth_score = 2
    elif depth_level == "medium":
        depth_score = 1
    else:
        depth_score = 0
    
    # Combine scores
    total = relatedness_score + correctness_score + depth_score
    
    # Apply confidence multiplier
    final_score = total * confidence
    
    return min(10.0, max(0.0, final_score))

def decide_next_question_type(score: float, depth: str, correctness: str) -> str:
    """Decide what type of question to ask next"""
    
    if score < 3:
        return "repeat_easier"
    elif score < 5 and depth == "shallow":
        return "follow_up_deeper"
    elif score < 5:
        return "follow_up_clarify"
    elif score >= 8:
        return "new_topic"
    else:
        return "follow_up"

# ===== CONSTANTS =====
QUESTION_TYPES = {
    "opening": "Initial question about background",
    "technical": "Technical/skill-based question",
    "follow_up": "Follow-up to previous answer",
    "behavioral": "Behavioral/situational question",
    "closing": "Final question"
}

DEPTH_LEVELS = {
    "shallow": "Very brief answer",
    "medium": "Reasonable detail",
    "deep": "Comprehensive answer"
}

CORRECTNESS_LEVELS = {
    "good": "Correct and relevant",
    "partial": "Partially correct",
    "poor": "Incorrect or irrelevant"
}

# ===== VALIDATION =====
def validate_job_description(text: str) -> bool:
    """Validate job description"""
    return isinstance(text, str) and len(text.strip()) > 10

def validate_candidate_name(name: str) -> bool:
    """Validate candidate name"""
    return isinstance(name, str) and len(name.strip()) > 2

def validate_duration(duration: int) -> bool:
    """Validate interview duration"""
    return isinstance(duration, int) and 3 <= duration <= 60
