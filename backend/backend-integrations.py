# backend/integrations.py
# External API Integrations

import aiohttp
import asyncio
from typing import Optional
import os

from config import settings
from utils import logger

# ===== WHISPER API (Speech-to-Text) =====
class WhisperAPI:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = "whisper-1"
        self.base_url = "https://api.openai.com/v1/audio/transcriptions"
    
    async def transcribe_streaming(self, audio_bytes):
        """Stream audio chunk to Whisper API"""
        try:
            if not self.api_key:
                logger.warning("OpenAI API key not set")
                return {"partial_transcription": ""}
            
            # In production, implement streaming
            return {"partial_transcription": ""}
        except Exception as e:
            logger.error(f"Whisper streaming error: {e}")
            return {"partial_transcription": ""}
    
    async def transcribe_full(self, audio_bytes):
        """Full transcription of audio"""
        try:
            if not self.api_key:
                logger.warning("OpenAI API key not set")
                return {"full_transcription": ""}
            
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                data = aiohttp.FormData()
                data.add_field('file', audio_bytes, filename='audio.wav')
                data.add_field('model', self.model)
                
                async with session.post(
                    self.base_url,
                    headers=headers,
                    data=data,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as resp:
                    result = await resp.json()
                    return {"full_transcription": result.get("text", "")}
        except Exception as e:
            logger.error(f"Whisper full transcription error: {e}")
            return {"full_transcription": ""}

# ===== HUGGINGFACE API (LLM + Semantic Analysis) =====
class HuggingFaceAPI:
    def __init__(self):
        self.api_key = settings.LLM_API_KEY
        self.base_url = "https://api-inference.huggingface.co/models"
        self.model = settings.LLM_MODEL
    
    async def generate(self, prompt: str, max_tokens: int = 256) -> str:
        """Generate text using HuggingFace LLM"""
        try:
            if not self.api_key:
                logger.warning("HuggingFace API key not set")
                return ""
            
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Bearer {self.api_key}"}
                payload = {
                    "inputs": prompt,
                    "parameters": {"max_new_tokens": max_tokens}
                }
                
                async with session.post(
                    f"{self.base_url}/{self.model}",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=settings.LLM_TIMEOUT)
                ) as resp:
                    result = await resp.json()
                    if isinstance(result, list) and len(result) > 0:
                        return result[0].get("generated_text", "")
                    return ""
        except Exception as e:
            logger.error(f"HuggingFace generation error: {e}")
            return ""
    
    async def semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts"""
        try:
            # Simplified version - in production use sentence-transformers
            # For now, return a mock similarity based on word overlap
            words1 = set(text1.lower().split())
            words2 = set(text2.lower().split())
            
            if not words1 or not words2:
                return 0.0
            
            intersection = len(words1 & words2)
            union = len(words1 | words2)
            similarity = intersection / union if union > 0 else 0.0
            
            return min(1.0, max(0.0, similarity))
        except Exception as e:
            logger.error(f"Semantic similarity error: {e}")
            return 0.5
    
    async def evaluate_correctness(self, question: str, response: str, job_description: str) -> dict:
        """Evaluate if response is correct"""
        try:
            prompt = f"""
            Job Description: {job_description}
            Question: {question}
            Answer: {response}
            
            Is this answer correct and relevant? Rate it as: good, partial, or poor.
            Also provide brief feedback.
            Format: RATING: [good/partial/poor]
            FEEDBACK: [your feedback]
            """
            
            result = await self.generate(prompt, max_tokens=100)
            
            if "good" in result.lower():
                rating = "good"
            elif "partial" in result.lower():
                rating = "partial"
            else:
                rating = "poor"
            
            feedback = result.split("FEEDBACK:")[-1].strip() if "FEEDBACK:" in result else "Good answer."
            
            return {
                "assessment": rating,
                "feedback": feedback
            }
        except Exception as e:
            logger.error(f"Correctness evaluation error: {e}")
            return {"assessment": "partial", "feedback": "Reasonable answer."}

# ===== PIPER TTS (Text-to-Speech) =====
class PiperTTS:
    def __init__(self):
        self.voice = settings.TTS_VOICE
        self.engine = settings.TTS_ENGINE
    
    async def synthesize(self, text: str, filename: str) -> Optional[str]:
        """Convert text to speech"""
        try:
            import subprocess
            import tempfile
            
            # Create temp directory for audio
            os.makedirs(settings.AUDIO_CACHE_DIR, exist_ok=True)
            output_path = os.path.join(settings.AUDIO_CACHE_DIR, f"{filename}.wav")
            
            # In production, use actual Piper TTS
            # For now, create a dummy file
            with open(output_path, 'wb') as f:
                f.write(b'RIFF' + b'\x00' * 1000)  # Dummy WAV file
            
            logger.info(f"Generated TTS: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"TTS synthesis error: {e}")
            return None

# ===== MUSETALK (Video Generation) =====
class MuseTalkAPI:
    def __init__(self):
        self.gpu = settings.MUSETALK_GPU
        self.fp16 = settings.MUSETALK_FP16
    
    async def generate(self, avatar_image: str, audio_path: str, output_path: str) -> Optional[str]:
        """Generate video from avatar image and audio"""
        try:
            import shutil
            
            # Create output directory
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # In production, use actual MuseTalk API
            # For now, create a dummy video file
            with open(output_path, 'wb') as f:
                f.write(b'\x00\x00\x00\x20ftypisom' + b'\x00' * 1000)  # Dummy MP4 file
            
            logger.info(f"Generated video: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"MuseTalk generation error: {e}")
            return None
