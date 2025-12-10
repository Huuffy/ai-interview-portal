import asyncio
import subprocess
import os
from typing import Optional
import logging
from pathlib import Path
import shutil

from config import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== MUSETALK API =====

class MuseTalkAPI:
    """Wrapper around MuseTalk CLI for video generation."""

    def __init__(self):
        self.musetalk_root = settings.MUSETALK_ROOT
        self.gpu = settings.MUSETALK_GPU
        self.fp16 = settings.MUSETALK_FP16
        self.python_bin = settings.MUSETALK_PYTHON_BIN
        self.inference_script = os.path.join(self.musetalk_root, "inference.py")
        logger.info(f"MuseTalk initialized: root={self.musetalk_root}, gpu={self.gpu}, fp16={self.fp16}")

    async def generate(
        self,
        avatar_image: str,
        audio_path: str,
        output_path: str,
        video_type: str = "standard"
    ) -> Optional[str]:
        """Generate lip-synced video from avatar image and audio."""
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
                logger.error(f"MuseTalk failed (code {result.returncode}): {result.stderr}")
                return None

            # Verify output file exists and has content
            if not os.path.exists(output_path):
                logger.error(f"Output file not created: {output_path}")
                return None

            file_size = os.path.getsize(output_path)
            if file_size < 100 * 1024:
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
            "checkpoints_dir": os.path.exists(os.path.join(self.musetalk_root, "checkpoints")),
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
        self.piper_bin = settings.PIPER_BIN
        
        logger.info(f"PiperTTS initialized: voice={self.voice}, piper_bin={self.piper_bin}")
        
        # Create audio cache directory
        os.makedirs(settings.AUDIO_CACHE_DIR, exist_ok=True)

    def _find_piper_executable(self) -> Optional[str]:
        """Find Piper executable in system."""
        # First, try the configured path
        if self.piper_bin and os.path.exists(self.piper_bin):
            logger.info(f"Found Piper at configured path: {self.piper_bin}")
            return self.piper_bin

        # Try to find in common locations on Windows
        if os.name == 'nt':  # Windows
            common_paths = [
                r"C:\Program Files\piper\piper.exe",
                r"C:\Program Files (x86)\piper\piper.exe",
                os.path.expanduser(r"~\AppData\Local\Programs\Piper\piper.exe"),
            ]
            for path in common_paths:
                if os.path.exists(path):
                    logger.info(f"Found Piper at: {path}")
                    return path

        # Try to find in PATH using 'where' (Windows) or 'which' (Linux/Mac)
        try:
            if os.name == 'nt':  # Windows
                result = subprocess.run(['where', 'piper'], capture_output=True, text=True, timeout=5)
            else:  # Linux/Mac
                result = subprocess.run(['which', 'piper'], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                piper_path = result.stdout.strip()
                logger.info(f"Found Piper in PATH: {piper_path}")
                return piper_path
        except Exception as e:
            logger.debug(f"Could not search PATH: {e}")

        logger.warning("Piper executable not found. Install with: pip install piper-tts")
        return None

    async def synthesize(self, text: str, output_path: str) -> Optional[str]:
        """Synthesize speech from text using Piper TTS."""
        try:
            # Create output directory
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Find piper executable
            piper_bin = self._find_piper_executable()
            if not piper_bin:
                logger.error("Piper TTS executable not found. Cannot synthesize.")
                # Fallback: create dummy audio file for testing
                logger.warning("Creating dummy audio file for testing purposes")
                with open(output_path, 'wb') as f:
                    # Create minimal WAV file header
                    f.write(b'RIFF')
                    f.write(b'\x24\x00\x00\x00')  # File size
                    f.write(b'WAVE')
                    f.write(b'fmt ')
                    f.write(b'\x10\x00\x00\x00')  # Subchunk1 size
                    f.write(b'\x01\x00')  # Audio format (PCM)
                    f.write(b'\x01\x00')  # Num channels
                    f.write(b'\x44\xac\x00\x00')  # Sample rate
                    f.write(b'\x88\x58\x01\x00')  # Byte rate
                    f.write(b'\x02\x00')  # Block align
                    f.write(b'\x10\x00')  # Bits per sample
                    f.write(b'data')
                    f.write(b'\x00\x00\x00\x00')  # Data size
                return output_path

            # Build command
            cmd = [
                piper_bin,
                "--model", self.voice,
                "--output_file", output_path,
                "--speed", str(self.speed)
            ]

            logger.info(f"Running Piper: {' '.join(cmd)}")

            # Execute Piper
            result = await asyncio.to_thread(
                subprocess.run,
                cmd,
                input=text,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                logger.error(f"Piper TTS failed (code {result.returncode}): {result.stderr}")
                return None

            if not os.path.exists(output_path):
                logger.error(f"Piper output file not created: {output_path}")
                return None

            file_size = os.path.getsize(output_path)
            logger.info(f"Generated audio: {output_path} ({file_size} bytes)")
            return output_path

        except subprocess.TimeoutExpired:
            logger.error(f"Piper TTS timeout: {text[:50]}...")
            return None
        except Exception as e:
            logger.error(f"Piper TTS error: {e}", exc_info=True)
            return None

    def get_piper_status(self) -> dict:
        """Check if Piper is properly installed and available."""
        piper_bin = self._find_piper_executable()
        status = {
            "available": piper_bin is not None,
            "executable": piper_bin,
            "voice": self.voice,
            "audio_cache_dir": settings.AUDIO_CACHE_DIR,
            "cache_writable": os.access(settings.AUDIO_CACHE_DIR, os.W_OK),
        }
        return status


# ===== WHISPER API =====

class WhisperAPI:
    """Speech-to-Text using OpenAI Whisper"""

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.WHISPER_MODEL
        logger.info(f"WhisperAPI initialized: model={self.model}")

    async def transcribe_streaming(self, audio_bytes: bytes) -> dict:
        """Transcribe audio chunk (for partial/streaming transcription)."""
        try:
            # In production, use real streaming Whisper API
            # For now, placeholder implementation
            return {"partial_transcription": ""}
        except Exception as e:
            logger.error(f"Whisper streaming error: {e}")
            return {"partial_transcription": ""}

    async def transcribe_full(self, audio_bytes: bytes) -> dict:
        """Transcribe full audio from combined chunks."""
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

    async def semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts (0-1)"""
        try:
            # Placeholder: in production use sentence-transformers
            # For MVP, return dummy value
            return 0.7
        except Exception as e:
            logger.error(f"Similarity error: {e}")
            return 0.5

    async def evaluate_correctness(self, question: str, response: str, job_description: str) -> dict:
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
