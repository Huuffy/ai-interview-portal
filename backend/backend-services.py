# backend/services.py
# All 8 Business Logic Services in One File

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid
import os

from config import settings
from integrations import WhisperAPI, HuggingFaceAPI, PiperTTS, MuseTalkAPI
from utils import logger, calculate_score, decide_next_question_type

# ===== 1. INTERVIEW SERVICE =====
class InterviewService:
    def __init__(self):
        self.interviews = {}
    
    def create_interview(self, session_id, job_description, candidate_name, duration_minutes):
        """Create interview in DB"""
        self.interviews[session_id] = {
            "session_id": session_id,
            "job_description": job_description,
            "candidate_name": candidate_name,
            "interview_duration_minutes": duration_minutes,
            "status": "setup",
            "start_time": datetime.now(),
            "end_time": None,
            "overall_score": None,
            "recommendation": None
        }
        return self.interviews[session_id]
    
    def complete_interview(self, session_id, results):
        """Update interview status to completed"""
        if session_id in self.interviews:
            self.interviews[session_id]["status"] = "completed"
            self.interviews[session_id]["end_time"] = datetime.now()
            self.interviews[session_id]["overall_score"] = results.get("overall_score")
            self.interviews[session_id]["recommendation"] = results.get("recommendation")
    
    def end_interview(self, session_id):
        """Handle early termination"""
        if session_id in self.interviews:
            self.interviews[session_id]["status"] = "aborted"
            self.interviews[session_id]["end_time"] = datetime.now()

# ===== 2. AUDIO SERVICE =====
class AudioService:
    def __init__(self):
        self.whisper = WhisperAPI()
        self.audio_buffer = {}
    
    async def transcribe_chunk(self, session_id, audio_bytes):
        """Stream audio chunk to Whisper, return partial transcription"""
        try:
            result = await self.whisper.transcribe_streaming(audio_bytes)
            return result.get("partial_transcription", "")
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return ""
    
    async def get_final_transcription(self, session_id, audio_chunks):
        """Get final transcription from all chunks"""
        try:
            audio_combined = b"".join(audio_chunks)
            result = await self.whisper.transcribe_full(audio_combined)
            return result.get("full_transcription", "")
        except Exception as e:
            logger.error(f"Final transcription error: {e}")
            return ""
    
    def detect_vad(self, audio_bytes, silence_threshold_ms=500):
        """Detect voice activity (silence > threshold = speech ended)"""
        # Simplified VAD - in production use webrtcvad or similar
        return True

# ===== 3. EVALUATION SERVICE =====
class EvaluationService:
    def __init__(self):
        self.hf = HuggingFaceAPI()
    
    async def evaluate_response(self, question, response, job_description, conversation_history):
        """
        Evaluate response on 3 dimensions:
        1. Relatedness (0-1): Did they answer the question?
        2. Correctness (0-10): Is it right/partial/wrong?
        3. Depth (shallow/medium/deep): How detailed?
        """
        try:
            # Check relatedness
            relatedness = await self.check_relatedness(question, response, job_description)
            
            if relatedness < 0.3:
                return {
                    "score": 2,
                    "marks": "2/10",
                    "correctness": "poor",
                    "relatedness": relatedness,
                    "depth": "none",
                    "next_question_type": "repeat_easier",
                    "feedback": "Response didn't address the question. Let's try another angle."
                }
            
            # Check correctness
            correctness = await self.assess_correctness(question, response, job_description)
            
            # Check depth
            depth = await self.assess_depth(question, response)
            
            # Calculate score
            score = calculate_score(relatedness, correctness, depth, confidence=0.85)
            
            # Decide next question type
            next_type = decide_next_question_type(
                score, depth.get("level"), correctness.get("assessment")
            )
            
            return {
                "score": round(score, 1),
                "marks": f"{round(score, 1)}/10",
                "correctness": correctness.get("assessment", "partial"),
                "relatedness": round(relatedness, 2),
                "depth": depth.get("level", "medium"),
                "next_question_type": next_type,
                "feedback": correctness.get("feedback", "Good response."),
                "confidence": 0.85
            }
        except Exception as e:
            logger.error(f"Evaluation error: {e}")
            return {
                "score": 5,
                "marks": "5/10",
                "correctness": "partial",
                "relatedness": 0.5,
                "depth": "medium",
                "next_question_type": "follow_up",
                "feedback": "Let's continue.",
                "confidence": 0.5
            }
    
    async def check_relatedness(self, question, response, job_description):
        """Semantic similarity: Does response relate to question?"""
        try:
            similarity = await self.hf.semantic_similarity(question, response)
            return min(1.0, max(0.0, similarity))
        except:
            return 0.5
    
    async def assess_correctness(self, question, response, job_description):
        """Check if response is correct/partial/wrong"""
        try:
            evaluation = await self.hf.evaluate_correctness(question, response, job_description)
            return evaluation
        except:
            return {"assessment": "partial", "feedback": "Reasonable answer."}
    
    async def assess_depth(self, question, response):
        """Determine response depth: shallow/medium/deep"""
        words = len(response.split())
        if words < 20:
            depth = "shallow"
        elif words < 80:
            depth = "medium"
        else:
            depth = "deep"
        
        return {"level": depth, "word_count": words}

# ===== 4. QUESTION SERVICE =====
class QuestionService:
    def __init__(self):
        self.hf = HuggingFaceAPI()
    
    async def generate_opening_question(self, job_description):
        """Generate opening question for interview"""
        try:
            prompt = f"""
            Job: {job_description}
            Generate a friendly opening interview question about the candidate's background and experience.
            Keep it conversational and open-ended.
            Return ONLY the question, nothing else.
            """
            question = await self.hf.generate(prompt)
            return question.strip()
        except:
            return "Tell me about your professional background and relevant experience."
    
    async def generate_adaptive_question(self, previous_question, response, evaluation, job_description, conversation_history):
        """Generate next question based on evaluation"""
        try:
            next_type = evaluation.get("next_question_type", "follow_up")
            
            if next_type == "new_topic":
                prompt = f"""
                Job: {job_description}
                Previous Q: {previous_question}
                User response: {response}
                
                Generate a different technical question on a new topic relevant to this job.
                Return ONLY the question.
                """
            
            elif next_type == "follow_up_deeper":
                prompt = f"""
                Previous Q: {previous_question}
                User response: {response}
                
                Generate a follow-up question that digs deeper into specifics, technical details, or challenges.
                Return ONLY the question.
                """
            
            elif next_type == "follow_up_clarify":
                prompt = f"""
                Previous Q: {previous_question}
                User response: {response}
                
                The user was vague. Generate a question asking for specific examples or details.
                Return ONLY the question.
                """
            
            elif next_type == "repeat_easier":
                prompt = f"""
                Previous Q: {previous_question}
                
                Rephrase this question in a simpler, easier way.
                Return ONLY the question.
                """
            
            else:
                prompt = f"Generate a follow-up question to: {previous_question}"
            
            question = await self.hf.generate(prompt)
            return question.strip()
        except:
            return "Can you elaborate on that experience?"
    
    async def pre_generate_opening_questions(self, session_id, job_description, count):
        """Pre-generate opening questions before interview"""
        questions = []
        for i in range(count):
            try:
                q = await self.generate_opening_question(job_description)
                questions.append(q)
            except:
                questions.append(f"Question {i+1}: Tell me about your experience.")
        return questions
    
    async def generate_closing_statement(self):
        """Generate closing message"""
        return "Thank you for your time. Let me evaluate your responses..."

# ===== 5. MEDIA SERVICE =====
class MediaService:
    def __init__(self):
        self.piper = PiperTTS()
        self.musetalk = MuseTalkAPI()
        self.video_cache = {}
    
    async def text_to_speech(self, text, filename):
        """Convert text to speech using Piper"""
        try:
            audio_path = await self.piper.synthesize(text, filename)
            return audio_path
        except Exception as e:
            logger.error(f"TTS error: {e}")
            return None
    
    async def generate_video_async(self, session_id, audio_path, filename):
        """Generate lip-synced video using MuseTalk (async)"""
        try:
            avatar_path = os.path.join(settings.AVATAR_DIR, "default_avatar.png")
            output_dir = os.path.join(settings.VIDEO_CACHE_DIR, session_id)
            os.makedirs(output_dir, exist_ok=True)
            
            video_path = await self.musetalk.generate(
                avatar_image=avatar_path,
                audio_path=audio_path,
                output_path=os.path.join(output_dir, f"{filename}.mp4")
            )
            self.video_cache[f"{session_id}_{filename}"] = video_path
            return video_path
        except Exception as e:
            logger.error(f"Video generation error: {e}")
            return None
    
    def get_cached_video(self, session_id, filename):
        """Get cached video"""
        key = f"{session_id}_{filename}"
        return self.video_cache.get(key)
    
    async def pre_generate_greeting(self, session_id):
        """Pre-generate greeting video before interview"""
        try:
            text = "Hello! Welcome to your interview. I'm your AI interviewer. Let's begin by learning about your background."
            audio_path = await self.text_to_speech(text, "greeting")
            if audio_path:
                video_path = await self.generate_video_async(session_id, audio_path, "greeting")
                return video_path
        except Exception as e:
            logger.error(f"Greeting generation error: {e}")
        return None
    
    async def generate_question_media(self, session_id, question_index, text):
        """Generate TTS and video for a question"""
        try:
            audio_path = await self.text_to_speech(text, f"q{question_index}")
            if audio_path:
                await self.generate_video_async(session_id, audio_path, f"q{question_index}")
        except Exception as e:
            logger.error(f"Question media generation error: {e}")
    
    def cleanup_old_videos(self, session_id):
        """Delete old videos to save space"""
        try:
            session_dir = os.path.join(settings.VIDEO_CACHE_DIR, session_id)
            if os.path.exists(session_dir):
                import shutil
                shutil.rmtree(session_dir)
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

# ===== 6. SESSION SERVICE =====
class SessionService:
    def __init__(self):
        self.sessions = {}
    
    def create_session(self, session_id, job_description, candidate_name):
        """Create new session"""
        self.sessions[session_id] = {
            "session_id": session_id,
            "job_description": job_description,
            "candidate_name": candidate_name,
            "questions": [],
            "responses": [],
            "evaluations": [],
            "created_at": datetime.now()
        }
        return self.sessions[session_id]
    
    def get_session(self, session_id):
        """Get session"""
        return self.sessions.get(session_id)
    
    def add_question(self, session_id, index, text):
        """Add question to session"""
        if session_id in self.sessions:
            self.sessions[session_id]["questions"].append({
                "index": index,
                "text": text,
                "created_at": datetime.now()
            })
    
    def get_question(self, session_id, index):
        """Get question by index"""
        if session_id not in self.sessions:
            return None
        questions = self.sessions[session_id]["questions"]
        for q in questions:
            if q["index"] == index:
                return q
        return None
    
    def add_response(self, session_id, question_index, text):
        """Add candidate response"""
        if session_id in self.sessions:
            self.sessions[session_id]["responses"].append({
                "question_index": question_index,
                "text": text,
                "created_at": datetime.now()
            })
    
    def add_evaluation(self, session_id, question_index, evaluation):
        """Add evaluation"""
        if session_id in self.sessions:
            self.sessions[session_id]["evaluations"].append({
                "question_index": question_index,
                **evaluation,
                "created_at": datetime.now()
            })
    
    def get_conversation_history(self, session_id):
        """Get full conversation history"""
        if session_id not in self.sessions:
            return {"questions": [], "responses": [], "evaluations": []}
        session = self.sessions[session_id]
        return {
            "questions": session["questions"],
            "responses": session["responses"],
            "evaluations": session["evaluations"]
        }

# ===== 7. TIMER SERVICE =====
class TimerService:
    def __init__(self):
        self.timers = {}
    
    def start_timer(self, session_id, duration_minutes):
        """Start interview timer"""
        self.timers[session_id] = {
            "start_time": datetime.now(),
            "duration_seconds": duration_minutes * 60,
            "closing_buffer": settings.CLOSING_BUFFER_SECONDS
        }
    
    def get_remaining(self, session_id):
        """Get remaining time in seconds"""
        if session_id not in self.timers:
            return 0
        timer = self.timers[session_id]
        elapsed = (datetime.now() - timer["start_time"]).total_seconds()
        remaining = timer["duration_seconds"] - elapsed
        return max(0, remaining)
    
    def should_close(self, session_id):
        """Check if time to close"""
        remaining = self.get_remaining(session_id)
        return remaining <= self.timers.get(session_id, {}).get("closing_buffer", 90)
    
    def is_overtime(self, session_id):
        """Check if interview exceeded time"""
        return self.get_remaining(session_id) <= 0

# ===== 8. RESULTS SERVICE =====
class ResultsService:
    def compile_results(self, session_id, session_service, evaluation_service):
        """Compile final results"""
        session = session_service.get_session(session_id)
        if not session:
            return {}
        
        evaluations = session.get("evaluations", [])
        
        # Calculate overall score
        scores = [e.get("score", 5) for e in evaluations]
        overall_score = sum(scores) / len(scores) if scores else 0
        
        # Generate recommendation
        if overall_score >= 7.5:
            recommendation = "STRONG HIRE"
        elif overall_score >= 7.0:
            recommendation = "HIRE"
        elif overall_score >= 5.0:
            recommendation = "CONSIDER"
        elif overall_score >= 3.0:
            recommendation = "HESITANT"
        else:
            recommendation = "NO HIRE"
        
        # Compile breakdown
        breakdown = []
        for q, e in zip(session.get("questions", []), evaluations):
            breakdown.append({
                "question": q.get("text", ""),
                "score": e.get("score", 5),
                "marks": e.get("marks", "5/10"),
                "feedback": e.get("feedback", "")
            })
        
        # Identify strengths/weaknesses
        strengths = [e.get("feedback", "") for e in evaluations if e.get("score", 5) >= 7]
        weaknesses = [e.get("feedback", "") for e in evaluations if e.get("score", 5) < 6]
        
        return {
            "overall_score": round(overall_score, 1),
            "recommendation": recommendation,
            "breakdown": breakdown,
            "strengths": strengths[:3],
            "weaknesses": weaknesses[:3]
        }
    
    def get_results(self, interview_id):
        """Get stored results"""
        # In production, fetch from database
        return None
    
    def export_pdf(self, interview_id):
        """Export results as PDF"""
        # In production, generate PDF file
        return None
