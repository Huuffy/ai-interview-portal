import asyncio
import subprocess
import os
from typing import Optional
import logging

from config import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== MUSETALK API =====

class MuseTalkAPI:
    """
    Wrapper around MuseTalk CLI for video generation.
    
    Converts audio + avatar image into lip-synced video using MuseTalk.
    
    Usage:
        musetalk = MuseTalkAPI()
        video_path = await musetalk.generate(
            avatar_image="/path/to/avatar.png",
            audio_path="/path/to/audio.wav",
            output_path="/path/to/output.mp4"
        )
    """
    
    def __init__(self):
        self.musetalk_root = settings.MUSETALK_ROOT
        self.gpu = settings.MUSETALK_GPU
        self.fp16 = settings.MUSETALK_FP16
        self.python_bin = settings.MUSETALK_PYTHON_BIN
        
        # Inference script path
        self.inference_script = os.path.join(
            self.musetalk_root, 
            "inference.py"
        )
        
        logger.info(
            f"MuseTalk initialized: root={self.musetalk_root}, "
            f"gpu={self.gpu}, fp16={self.fp16}"
        )
    
    async def generate(
        self, 
        avatar_image: str, 
        audio_path: str, 
        output_path: str,
        video_type: str = "standard"
    ) -> Optional[str]:
        """
        Generate lip-synced video from avatar image and audio.
        
        Args:
            avatar_image: Path to reference face image (PNG/JPG)
            audio_path: Path to audio file (WAV recommended)
            output_path: Where to save the output MP4
            video_type: Quality/speed tradeoff (standard, hd, fast)
        
        Returns:
            output_path if successful, None if failed
        """
        try:
            # Validate inputs
            if not os.path.exists(avatar_image):
                logger.error(f"Avatar image not found: {avatar_image}")
                return None
            
            if not os.path.exists(audio_path):
                logger.error(f"Audio file not found: {audio_path}")
                return None
            
            # Create output directory
            output_dir = os.path.dirname(output_path)
            os.makedirs(output_dir, exist_ok=True)
            
            # Build CLI command
            cmd = [
                self.python_bin,
                self.inference_script,
                "--avatar", avatar_image,
                "--audio", audio_path,
                "--output", output_path,
                "--gpu", str(self.gpu),
            ]
            
            # Add optional flags
            if self.fp16:
                cmd.append("--fp16")
            
            if video_type == "hd":
                cmd.extend(["--resolution", "1024"])
            elif video_type == "fast":
                cmd.extend(["--fps", "24"])
            
            logger.info(f"Running MuseTalk: {' '.join(cmd[:7])}...")
            
            # Execute with timeout (5 minutes max)
            result = await asyncio.to_thread(
                subprocess.run,
                cmd,
                cwd=self.musetalk_root,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            # Check result
            if result.returncode != 0:
                logger.error(
                    f"MuseTalk failed (code {result.returncode}): {result.stderr}"
                )
                return None
            
            # Verify output file exists and has content
            if not os.path.exists(output_path):
                logger.error(f"Output file not created: {output_path}")
                return None
            
            file_size = os.path.getsize(output_path)
            if file_size < 100 * 1024:  # Less than 100KB is suspicious
                logger.warning(f"Output file small ({file_size} bytes): {output_path}")
            
            logger.info(f"Generated video: {output_path} ({file_size} bytes)")
            return output_path
            
        except subprocess.TimeoutExpired:
            logger.error(f"MuseTalk timeout after 300s: {audio_path}")
            return None
        except Exception as e:
            logger.error(f"MuseTalk generation failed: {e}", exc_info=True)
            return None
    
    def get_musetalk_status(self) -> dict:
        """Check if MuseTalk is properly installed and configured."""
        status = {
            "installed": os.path.exists(self.musetalk_root),
            "inference_script": os.path.exists(self.inference_script),
            "checkpoints_dir": os.path.exists(
                os.path.join(self.musetalk_root, "checkpoints")
            ),
            "gpu_available": self._check_gpu_available(),
        }
        return status
    
    def _check_gpu_available(self) -> bool:
        """Check if CUDA GPU is available."""
        try:
            import torch
            return torch.cuda.is_available()
        except:
            return False


# ===== PIPER TTS API =====

class PiperTTS:
    """Text-to-Speech using Piper TTS (offline, fast)"""
    
    def __init__(self):
        self.voice = settings.PIPER_VOICE
        self.speed = settings.PIPER_SPEED
        logger.info(f"PiperTTS initialized: voice={self.voice}")
    
    async def synthesize(
        self, 
        text: str, 
        output_path: str
    ) -> Optional[str]:
        """
        Synthesize speech from text using Piper TTS.
        
        Args:
            text: Text to synthesize
            output_path: Where to save the WAV file
        
        Returns:
            output_path if successful, None if failed
        """
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Use Piper CLI: echo "text" | piper --model voice.onnx --output_file output.wav
            cmd = [
                "piper",
                "--model", self.voice,
                "--output_file", output_path,
                "--speed", str(self.speed)
            ]
            
            result = await asyncio.to_thread(
                subprocess.run,
                cmd,
                input=text,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.error(f"Piper TTS failed: {result.stderr}")
                return None
            
            if not os.path.exists(output_path):
                logger.error(f"Piper output file not created: {output_path}")
                return None
            
            logger.info(f"Generated audio: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Piper TTS error: {e}")
            return None


# ===== WHISPER API =====

class WhisperAPI:
    """Speech-to-Text using OpenAI Whisper"""
    
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.WHISPER_MODEL
        logger.info(f"WhisperAPI initialized: model={self.model}")
    
    async def transcribe_streaming(
        self, 
        audio_bytes: bytes
    ) -> dict:
        """
        Transcribe audio chunk (for partial/streaming transcription).
        
        Returns: {"partial_transcription": "..."}
        """
        try:
            # In production, use real streaming Whisper API
            # For now, placeholder implementation
            return {"partial_transcription": ""}
        except Exception as e:
            logger.error(f"Whisper streaming error: {e}")
            return {"partial_transcription": ""}
    
    async def transcribe_full(
        self, 
        audio_bytes: bytes
    ) -> dict:
        """
        Transcribe full audio from combined chunks.
        
        Returns: {"full_transcription": "..."}
        """
        try:
            # Save audio to temp file
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(audio_bytes)
                temp_path = f.name
            
            # Call Whisper CLI
            cmd = [
                "whisper",
                temp_path,
                "--model", self.model,
                "--output_format", "json"
            ]
            
            result = await asyncio.to_thread(
                subprocess.run,
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Clean up temp file
            os.unlink(temp_path)
            
            if result.returncode != 0:
                logger.error(f"Whisper failed: {result.stderr}")
                return {"full_transcription": ""}
            
            # Parse JSON output
            import json
            output = json.loads(result.stdout)
            transcription = output.get("text", "")
            
            logger.info(f"Transcribed: {transcription[:50]}...")
            return {"full_transcription": transcription}
            
        except Exception as e:
            logger.error(f"Whisper transcription error: {e}")
            return {"full_transcription": ""}


# ===== HUGGINGFACE API =====

class HuggingFaceAPI:
    """LLM inference using HuggingFace models"""
    
    def __init__(self):
        self.api_key = settings.HUGGINGFACE_API_KEY
        self.model = settings.HUGGINGFACE_MODEL
        logger.info(f"HuggingFaceAPI initialized: model={self.model}")
    
    async def semantic_similarity(
        self, 
        text1: str, 
        text2: str
    ) -> float:
        """Calculate semantic similarity between two texts (0-1)"""
        try:
            # Placeholder: in production use sentence-transformers
            # For MVP, return dummy value
            return 0.7
        except Exception as e:
            logger.error(f"Similarity error: {e}")
            return 0.5
    
    async def evaluate_correctness(
        self, 
        question: str, 
        response: str, 
        job_description: str
    ) -> dict:
        """Evaluate if response is correct/partial/wrong"""
        try:
            # Placeholder implementation
            return {
                "assessment": "partial",
                "feedback": "Good response, could provide more details."
            }
        except Exception as e:
            logger.error(f"Evaluation error: {e}")
            return {
                "assessment": "partial",
                "feedback": "Unable to evaluate."
            }
    
    async def generate(self, prompt: str) -> str:
        """Generate text from prompt using LLM"""
        try:
            # Placeholder implementation
            return "This is a generated response."
        except Exception as e:
            logger.error(f"Generation error: {e}")
            return "Error generating response."
