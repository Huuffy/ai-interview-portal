# backend/services.py

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
        logger.info(f"[Interview] Created: {session_id}")
        return self.interviews[session_id]

    def complete_interview(self, session_id, results):
        """Update interview status to completed"""
        if session_id in self.interviews:
            self.interviews[session_id]["status"] = "completed"
            self.interviews[session_id]["end_time"] = datetime.now()
            self.interviews[session_id]["overall_score"] = results.get("overall_score")
            self.interviews[session_id]["recommendation"] = results.get("recommendation")
            logger.info(f"[Interview] Completed: {session_id}")

    def end_interview(self, session_id):
        """Handle early termination"""
        if session_id in self.interviews:
            self.interviews[session_id]["status"] = "aborted"
            self.interviews[session_id]["end_time"] = datetime.now()
            logger.info(f"[Interview] Aborted: {session_id}")

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
            logger.error(f"[Audio] Transcription error: {e}")
            return ""

    async def get_final_transcription(self, session_id, audio_chunks):
        """Get final transcription from all chunks"""
        try:
            audio_combined = b"".join(audio_chunks)
            result = await self.whisper.transcribe_full(audio_combined)
            return result.get("full_transcription", "")
        except Exception as e:
            logger.error(f"[Audio] Final transcription error: {e}")
            return ""

# ===== 3. EVALUATION SERVICE =====

class EvaluationService:
    def __init__(self):
        self.hf = HuggingFaceAPI()

    async def evaluate_response(self, question, response, job_description, conversation_history):
        """Evaluate response on 3 dimensions"""
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
            logger.error(f"[Evaluation] Error: {e}")
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
        """Semantic similarity"""
        try:
            similarity = await self.hf.semantic_similarity(question, response)
            return min(1.0, max(0.0, similarity))
        except:
            return 0.5

    async def assess_correctness(self, question, response, job_description):
        """Check if response is correct"""
        try:
            evaluation = await self.hf.evaluate_correctness(question, response, job_description)
            return evaluation
        except:
            return {"assessment": "partial", "feedback": "Reasonable answer."}

    async def assess_depth(self, question, response):
        """Determine response depth"""
        words = len(response.split())
        if words < 20:
            depth = "shallow"
        elif words < 80:
            depth = "medium"
        else:
            depth = "deep"
        return {"level": depth, "word_count": words}

# ===== 4. QUESTION SERVICE (FIXED) =====

class QuestionService:
    def __init__(self):
        self.hf = HuggingFaceAPI()

    async def get_question_by_index(self, session_id, index, session_service):
        """
        Retrieves a question text by index.
        IMPORTANT: This requires session_service to be passed to access the DB.
        """
        try:
            question_data = session_service.get_question(session_id, index)
            if question_data:
                return question_data.get("text")
            logger.warning(f"[Question] Question {index} not found for session {session_id}")
            return None
        except Exception as e:
            logger.error(f"[Question] Error retrieving question {index}: {e}")
            return None

    async def generate_opening_question(self, job_description):
        """Generate opening question"""
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
                prompt = f"""Job: {job_description}
Previous Q: {previous_question}
User response: {response}
Generate a different technical question on a new topic relevant to this job.
Return ONLY the question."""
            elif next_type == "follow_up_deeper":
                prompt = f"""Previous Q: {previous_question}
User response: {response}
Generate a follow-up question that digs deeper into specifics, technical details, or challenges.
Return ONLY the question."""
            else:
                prompt = f"Generate a follow-up question to: {previous_question}"
            
            question = await self.hf.generate(prompt)
            return question.strip()
        except:
            return "Can you elaborate on that experience?"

    async def pre_generate_opening_questions(self, session_id, job_description, count):
        """Pre-generate opening questions"""
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

# ===== 5. MEDIA SERVICE (VIDEO + AUDIO GENERATION) =====

class MediaService:
    def __init__(self):
        self.piper = PiperTTS()
        self.musetalk = MuseTalkAPI()
        self.video_cache = {}

    async def text_to_speech(self, text, session_id, filename):
        """Convert text to speech using Piper"""
        try:
            audio_path = os.path.join(settings.AUDIO_CACHE_DIR, session_id, f"{filename}.wav")
            os.makedirs(os.path.dirname(audio_path), exist_ok=True)
            
            logger.info(f"[Media] TTS: {filename}")
            # Ensure text is clean
            clean_text = text.strip().replace('"', '').replace("'", "")
            result = await self.piper.synthesize(clean_text, audio_path)
            
            if result:
                logger.info(f"✓ [Media] TTS completed: {filename}")
            else:
                logger.error(f"✗ [Media] TTS failed: {filename}")
            
            return result
        except Exception as e:
            logger.error(f"[Media] TTS error: {e}")
            return None

    async def generate_video(self, session_id, audio_path, video_filename):
        """Generate lip-synced video using MuseTalk"""
        try:
            avatar_path = os.path.join(settings.AVATAR_DIR, "default_avatar.png")
            
            # Check if avatar exists
            if not os.path.exists(avatar_path):
                logger.error(f"✗ [Media] Avatar not found: {avatar_path}")
                logger.error(f"  Please add default_avatar.png to {settings.AVATAR_DIR}/")
                return None
            
            output_dir = os.path.join(settings.VIDEO_CACHE_DIR, session_id)
            os.makedirs(output_dir, exist_ok=True)
            
            video_path = os.path.join(output_dir, f"{video_filename}.mp4")
            
            logger.info(f"[Media] Generating video: {video_filename}")
            logger.info(f"  Avatar: {avatar_path}")
            logger.info(f"  Audio: {audio_path}")
            logger.info(f"  Output: {video_path}")
            
            # Generate with MuseTalk
            result = await self.musetalk.generate(
                avatar_image=avatar_path,
                audio_path=audio_path,
                output_path=video_path,
                video_type="standard"
            )
            
            if result:
                self.video_cache[f"{session_id}_{video_filename}"] = video_path
                logger.info(f"✓ [Media] Video generated: {video_filename}")
            else:
                logger.error(f"✗ [Media] Video generation failed: {video_filename}")
            
            return result
        except Exception as e:
            logger.error(f"[Media] Video generation error: {e}", exc_info=True)
            return None

    async def generate_listening_video(self, session_id, audio_duration_seconds, video_filename):
        """Generate listening video (nodding head)"""
        try:
            avatar_path = os.path.join(settings.AVATAR_DIR, "default_avatar.png")
            
            if not os.path.exists(avatar_path):
                logger.error(f"✗ [Media] Avatar not found for listening video")
                return None
            
            output_dir = os.path.join(settings.VIDEO_CACHE_DIR, session_id)
            os.makedirs(output_dir, exist_ok=True)
            
            video_path = os.path.join(output_dir, f"{video_filename}.mp4")
            
            logger.info(f"[Media] Generating listening video: {video_filename}")
            logger.info(f"  Duration: {audio_duration_seconds}s")
            
            # Generate listening video
            result = await self.musetalk.generate_listening_video(
                avatar_image=avatar_path,
                audio_duration_seconds=audio_duration_seconds,
                output_path=video_path
            )
            
            if result:
                self.video_cache[f"{session_id}_{video_filename}"] = video_path
                logger.info(f"✓ [Media] Listening video generated: {video_filename}")
            else:
                logger.error(f"✗ [Media] Listening video failed: {video_filename}")
            
            return result
        except Exception as e:
            logger.error(f"[Media] Listening video error: {e}", exc_info=True)
            return None

    async def pre_generate_greeting(self, session_id):
        """Pre-generate greeting video before interview"""
        try:
            logger.info(f"[Media] Pre-generating greeting for {session_id}")
            
            text = "Hello! Welcome to your interview. I'm your AI interviewer. Let's begin by learning about your background and experience."
            
            # Generate audio
            audio_path = await self.text_to_speech(text, session_id, "greeting")
            
            if audio_path:
                # Generate video
                video_path = await self.generate_video(session_id, audio_path, "greeting")
                if video_path:
                    logger.info(f"[Media] Greeting ready: {video_path}")
                    return video_path
                else:
                    logger.error(f"✗ [Media] Greeting video failed")
            else:
                logger.error(f"✗ [Media] Greeting audio generation failed")
                return None
        
        except Exception as e:
            logger.error(f"[Media] Greeting generation error: {e}", exc_info=True)
            return None

    async def generate_question_media(self, session_id, question_index, text):
        """Generate TTS and video for a question"""
        try:
            logger.info(f"[Media] Generating question {question_index} media")
            
            # Generate audio
            audio_path = await self.text_to_speech(text, session_id, f"q{question_index}")
            
            if audio_path:
                # Generate video
                await self.generate_video(session_id, audio_path, f"q{question_index}")
            else:
                logger.error(f"✗ [Media] Question {question_index} audio generation failed")
        
        except Exception as e:
            logger.error(f"[Media] Question generation error: {e}", exc_info=True)

    async def generate_closing_media(self, session_id):
        """Generate closing statement video"""
        try:
            logger.info(f"[Media] Generating closing media")
            
            text = "Thank you for your time today. We'll evaluate your responses and get back to you soon. Good luck!"
            
            # Generate audio
            audio_path = await self.text_to_speech(text, session_id, "closing")
            
            if audio_path:
                # Generate video
                await self.generate_video(session_id, audio_path, "closing")
            else:
                logger.error(f"✗ [Media] Closing audio generation failed")
        
        except Exception as e:
            logger.error(f"[Media] Closing generation error: {e}", exc_info=True)

    def cleanup_old_videos(self, session_id):
        """Delete old videos to save space"""
        try:
            session_dir = os.path.join(settings.VIDEO_CACHE_DIR, session_id)
            if os.path.exists(session_dir):
                import shutil
                shutil.rmtree(session_dir)
                logger.info(f"[Media] Cleaned up videos for {session_id}")
        except Exception as e:
            logger.error(f"[Media] Cleanup error: {e}")

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
        logger.info(f"[Session] Created: {session_id}")
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
            logger.info(f"[Session] Added question {index}")

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
            logger.info(f"[Session] Added response to question {question_index}")

    def add_evaluation(self, session_id, question_index, evaluation):
        """Add evaluation"""
        if session_id in self.sessions:
            self.sessions[session_id]["evaluations"].append({
                "question_index": question_index,
                **evaluation,
                "created_at": datetime.now()
            })
            logger.info(f"[Session] Added evaluation for question {question_index}")

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
        logger.info(f"[Timer] Started for {session_id}: {duration_minutes} minutes")

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

    def stop_timer(self, session_id):
        """Stop and clean up timer"""
        if session_id in self.timers:
            del self.timers[session_id]
            logger.info(f"[Timer] Stopped for {session_id}")

# ===== 8. RESULTS SERVICE =====

class ResultsService:
    def compile_results(self, session_id, session_service=None):
        """Compile final results"""
        if session_service is None:
            return {}
        
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
        
        logger.info(f"[Results] Compiled for {session_id}: {overall_score:.1f}/10 ({recommendation})")
        
        return {
            "overall_score": round(overall_score, 1),
            "recommendation": recommendation,
            "evaluations": breakdown,
            "compiled_at": datetime.now().isoformat()
        }

    def get_results(self, interview_id):
        """Get stored results"""
        # TODO: Implement database storage
        return None

    def export_pdf(self, interview_id):
        """Export results as PDF"""
        # TODO: Implement PDF generation
        return None