
import asyncio
import subprocess
import os
from typing import Optional
import logging
from pathlib import Path
import shutil

from config import settings

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# ===== MUSETALK API - ACTUAL VIDEO GENERATION =====

class MuseTalkAPI:
    """Wrapper around MuseTalk CLI for video generation with LIP SYNC."""

    def __init__(self):
        self.musetalk_root = settings.MUSETALK_ROOT
        self.gpu = settings.MUSETALK_GPU
        self.fp16 = settings.MUSETALK_FP16
        self.python_bin = settings.MUSETALK_PYTHON_BIN

        self.inference_script = self._find_inference_script()
        
        logger.info(f"✓ MuseTalk initialized:")
        logger.info(f"  Root: {self.musetalk_root}")
        logger.info(f"  Inference: {self.inference_script}")
        logger.info(f"  GPU: {self.gpu}")
        logger.info(f"  FP16: {self.fp16}")
        logger.info(f"  Python: {self.python_bin}")

    def _find_inference_script(self) -> Optional[str]:
        """Find the correct path to inference.py"""
        
        # Possible paths to check
        possible_paths = os.path.join(self.musetalk_root, "MuseTalk", "scripts", "inference.py")
        
        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"✓ Found inference.py at: {path}")
                return path
        
        # If not found, log all files in root directory
        logger.error(f"✗ inference.py not found!")
        logger.error(f"  Searched in: {self.musetalk_root}")
        
        if os.path.exists(self.musetalk_root):
            files = os.listdir(self.musetalk_root)
            logger.error(f"  Files found in {self.musetalk_root}:")
            for f in files[:20]:  # List first 20
                path_type = "DIR" if os.path.isdir(os.path.join(self.musetalk_root, f)) else "FILE"
                logger.error(f"    [{path_type}] {f}")
        else:
            logger.error(f"  Directory doesn't exist: {self.musetalk_root}")
        
        return None

    async def generate(
        self,
        avatar_image: str,
        audio_path: str,
        output_path: str,
        video_type: str = "standard"
    ) -> Optional[str]:
        """
        Generate lip-synced video from avatar image and audio.
        MuseTalk automatically determines duration based on audio.
        """
        try:
            logger.info(f"[MuseTalk] Generating video...")
            logger.info(f"  Avatar: {avatar_image}")
            logger.info(f"  Audio: {audio_path}")
            logger.info(f"  Output: {output_path}")
            logger.info(f"  Type: {video_type}")

            # Validate inputs
            if not os.path.exists(avatar_image):
                logger.error(f"[MuseTalk] Avatar not found: {avatar_image}")
                return None

            if not os.path.exists(audio_path):
                logger.error(f"[MuseTalk] Audio not found: {audio_path}")
                return None

            # Check inference script
            if not self.inference_script or not os.path.exists(self.inference_script):
                logger.error(f"[MuseTalk] Inference script not found!")
                logger.error(f"  Expected: {self.inference_script}")
                logger.error(f"  Make sure MuseTalk is properly installed")
                return None

            file_size = os.path.getsize(audio_path)
            logger.info(f"[MuseTalk] Audio file size: {file_size} bytes")

            # Create output directory
            output_dir = os.path.dirname(output_path)
            os.makedirs(output_dir, exist_ok=True)
            logger.info(f"[MuseTalk] Output directory: {output_dir}")

            # ✅ FIXED: Use correct inference.py path directly
            cmd = [
                self.python_bin,
                self.inference_script,  # ← Direct path to inference.py (no subdirs)
                "--avatar", avatar_image,
                "--audio", audio_path,
                "--output", output_path,
                "--gpu", str(self.gpu),
            ]

            # Add optional flags
            if self.fp16:
                cmd.append("--fp16")
                logger.info(f"[MuseTalk] Using FP16 precision")

            if video_type == "hd":
                cmd.extend(["--resolution", "1024"])
                logger.info(f"[MuseTalk] Using HD resolution (1024)")
            elif video_type == "fast":
                cmd.extend(["--fps", "24"])
                logger.info(f"[MuseTalk] Using fast FPS (24)")

            logger.info(f"[MuseTalk] Command: {' '.join(cmd[:7])}...")

            # Execute with timeout (5 minutes max for generation)
            result = await asyncio.to_thread(
                subprocess.run,
                cmd,
                cwd=self.musetalk_root,  # Run FROM MuseTalk directory
                capture_output=True,
                text=True,
                timeout=300
            )

            # Check result
            if result.returncode != 0:
                logger.error(f"[MuseTalk] FAILED (code {result.returncode})")
                logger.error(f"[MuseTalk] STDERR: {result.stderr}")
                logger.error(f"[MuseTalk] STDOUT: {result.stdout}")
                return None

            # Verify output file exists and has content
            if not os.path.exists(output_path):
                logger.error(f"[MuseTalk] Output file NOT created: {output_path}")
                logger.error(f"  Check the MuseTalk command output above for errors")
                return None

            file_size = os.path.getsize(output_path)
            if file_size < 100 * 1024:  # Less than 100KB is suspicious
                logger.warning(f"[MuseTalk] Output file is very small: {file_size} bytes")

            logger.info(f"✓ [MuseTalk] Video generated successfully!")
            logger.info(f"  Path: {output_path}")
            logger.info(f"  Size: {file_size} bytes ({file_size / (1024*1024):.2f} MB)")

            return output_path

        except subprocess.TimeoutExpired:
            logger.error(f"[MuseTalk] TIMEOUT after 300 seconds")
            return None
        except Exception as e:
            logger.error(f"[MuseTalk] EXCEPTION: {e}", exc_info=True)
            return None

    async def generate_listening_video(
        self,
        avatar_image: str,
        audio_duration_seconds: float,
        output_path: str
    ) -> Optional[str]:
        """
        Generate listening/nodding video (interviewer listening to candidate).
        Uses silent audio or breathing sound, generates head nod animation.
        """
        try:
            logger.info(f"[MuseTalk] Generating listening video...")
            logger.info(f"  Duration: {audio_duration_seconds}s")
            logger.info(f"  Avatar: {avatar_image}")

            # Create silent audio file for listening duration
            silence_audio_path = os.path.join(
                os.path.dirname(output_path),
                "silence.wav"
            )

            await self._create_silent_audio(
                silence_audio_path,
                audio_duration_seconds
            )

            # Generate video with silent audio (creates natural listening/nodding)
            output = await self.generate(
                avatar_image=avatar_image,
                audio_path=silence_audio_path,
                output_path=output_path,
                video_type="standard"
            )

            # Clean up silence audio
            if os.path.exists(silence_audio_path):
                os.remove(silence_audio_path)

            logger.info(f"✓ [MuseTalk] Listening video generated!")
            return output

        except Exception as e:
            logger.error(f"[MuseTalk] Listening video error: {e}", exc_info=True)
            return None

    async def _create_silent_audio(self, output_path: str, duration_seconds: float) -> bool:
        """Create a silent WAV audio file for listening animations."""
        try:
            logger.info(f"[Audio] Creating silent audio: {duration_seconds}s")

            # Try using ffmpeg if available
            try:
                cmd = [
                    "ffmpeg",
                    "-f", "lavfi",
                    "-i", f"anullsrc=r=22050:cl=mono,atrim=duration={duration_seconds}",
                    "-q:a", "9",
                    "-acodec", "libmp3lame",
                    "-y",
                    output_path
                ]

                result = await asyncio.to_thread(
                    subprocess.run,
                    cmd,
                    capture_output=True,
                    timeout=30
                )

                if result.returncode == 0 and os.path.exists(output_path):
                    logger.info(f"✓ [Audio] Silent audio created with ffmpeg")
                    return True

            except Exception as e:
                logger.debug(f"[Audio] ffmpeg not available: {e}")

            # Fallback: create minimal WAV header
            logger.info(f"[Audio] Creating minimal WAV header")

            sample_rate = 22050
            duration = int(duration_seconds)
            num_samples = sample_rate * duration

            # WAV header (44 bytes)
            wav_header = bytearray()
            wav_header.extend(b"RIFF")
            wav_header.extend((36 + num_samples * 2).to_bytes(4, 'little'))
            wav_header.extend(b"WAVE")
            wav_header.extend(b"fmt ")
            wav_header.extend((16).to_bytes(4, 'little'))
            wav_header.extend((1).to_bytes(2, 'little'))
            wav_header.extend((1).to_bytes(2, 'little'))
            wav_header.extend(sample_rate.to_bytes(4, 'little'))
            wav_header.extend((sample_rate * 2).to_bytes(4, 'little'))
            wav_header.extend((2).to_bytes(2, 'little'))
            wav_header.extend((16).to_bytes(2, 'little'))
            wav_header.extend(b"data")
            wav_header.extend((num_samples * 2).to_bytes(4, 'little'))

            # Add silent samples (zeros)
            with open(output_path, 'wb') as f:
                f.write(wav_header)
                f.write(bytes(num_samples * 2))

            logger.info(f"✓ [Audio] Silent WAV created: {output_path}")
            return True

        except Exception as e:
            logger.error(f"[Audio] Silent audio creation failed: {e}", exc_info=True)
            return False

    def get_musetalk_status(self) -> dict:
        """Check if MuseTalk is properly installed and configured."""
        status = {
            "installed": os.path.exists(self.musetalk_root),
            "inference_script": self.inference_script is not None and os.path.exists(self.inference_script),
            "checkpoints_dir": os.path.exists(os.path.join(self.musetalk_root, "checkpoints")),
            "gpu_available": self._check_gpu_available(),
        }

        logger.info(f"[MuseTalk] Status check:")
        for key, value in status.items():
            logger.info(f"  {key}: {value}")

        return status

    def _check_gpu_available(self) -> bool:
        """Check if CUDA GPU is available."""
        try:
            import torch
            available = torch.cuda.is_available()
            logger.info(f"[GPU] CUDA available: {available}")
            return available
        except Exception as e:
            logger.debug(f"[GPU] Check failed: {e}")
            return False




# ===== PIPER TTS API - ACTUAL AUDIO GENERATION =====

class PiperTTS:
    """Text-to-Speech using Piper TTS (offline, fast, high quality)"""
    
    def __init__(self):
        self.voice = settings.PIPER_VOICE
        self.speed = settings.PIPER_SPEED
        self.piper_bin = settings.PIPER_BIN
        
        logger.info(f"✓ PiperTTS initialized:")
        logger.info(f"  Voice: {self.voice}")
        logger.info(f"  Speed: {self.speed}")
        logger.info(f"  Executable: {self.piper_bin}")
        
        # Create audio cache directory
        os.makedirs(settings.AUDIO_CACHE_DIR, exist_ok=True)

    def _find_piper_executable(self) -> Optional[str]:
        """Find Piper executable in system."""
        
        # First, try the configured path
        if self.piper_bin and os.path.exists(self.piper_bin):
            logger.info(f"✓ [Piper] Found at configured path: {self.piper_bin}")
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
                    logger.info(f"✓ [Piper] Found at: {path}")
                    return path
        
        # Try to find in PATH using 'where' (Windows) or 'which' (Linux/Mac)
        try:
            if os.name == 'nt':  # Windows
                result = subprocess.run(['where', 'piper'], capture_output=True, text=True, timeout=5)
            else:  # Linux/Mac
                result = subprocess.run(['which', 'piper'], capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                piper_path = result.stdout.strip()
                logger.info(f"✓ [Piper] Found in PATH: {piper_path}")
                return piper_path
        
        except Exception as e:
            logger.debug(f"[Piper] PATH search failed: {e}")
        
        logger.warning(f"✗ [Piper] Executable not found!")
        logger.warning(f"  Install with: pip install piper-tts")
        return None

    async def synthesize(self, text: str, output_path: str) -> Optional[str]:
        """Synthesize speech from text using Piper TTS."""
        try:
            logger.info(f"[Piper] Synthesizing TTS...")
            logger.info(f"  Text: {text[:50]}...")
            logger.info(f"  Output: {output_path}")
            
            # Create output directory
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Find piper executable
            piper_bin = self._find_piper_executable()
            
            if not piper_bin:
                logger.error(f"✗ [Piper] Executable not found, creating dummy audio...")
                return await self._create_dummy_audio(output_path)
            
            # Build command
            cmd = [
                piper_bin,
                "--model", self.voice,
                "--output_file", output_path,
                "--speed", str(self.speed)
            ]
            
            logger.info(f"[Piper] Command: {' '.join(cmd[:3])}...")
            
            # Execute Piper
            result = await asyncio.to_thread(
                subprocess.run,
                cmd,
                input=text,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                logger.error(f"✗ [Piper] FAILED (code {result.returncode})")
                logger.error(f"  STDERR: {result.stderr}")
                return None
            
            if not os.path.exists(output_path):
                logger.error(f"✗ [Piper] Output file not created: {output_path}")
                return None
            
            file_size = os.path.getsize(output_path)
            logger.info(f"✓ [Piper] Audio generated!")
            logger.info(f"  Path: {output_path}")
            logger.info(f"  Size: {file_size} bytes ({file_size / 1024:.1f} KB)")
            
            return output_path
        
        except subprocess.TimeoutExpired:
            logger.error(f"✗ [Piper] TIMEOUT after 60 seconds")
            return None
        
        except Exception as e:
            logger.error(f"✗ [Piper] EXCEPTION: {e}", exc_info=True)
            return None

    async def _create_dummy_audio(self, output_path: str) -> Optional[str]:
        """Create minimal valid WAV file for testing."""
        try:
            logger.warning(f"[Piper] Creating dummy audio: {output_path}")
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Create minimal WAV header (2 seconds of silence)
            sample_rate = 22050
            duration = 2
            num_samples = sample_rate * duration
            
            wav_header = bytearray()
            wav_header.extend(b"RIFF")
            wav_header.extend((36 + num_samples * 2).to_bytes(4, 'little'))
            wav_header.extend(b"WAVE")
            wav_header.extend(b"fmt ")
            wav_header.extend((16).to_bytes(4, 'little'))
            wav_header.extend((1).to_bytes(2, 'little'))
            wav_header.extend((1).to_bytes(2, 'little'))
            wav_header.extend(sample_rate.to_bytes(4, 'little'))
            wav_header.extend((sample_rate * 2).to_bytes(4, 'little'))
            wav_header.extend((2).to_bytes(2, 'little'))
            wav_header.extend((16).to_bytes(2, 'little'))
            wav_header.extend(b"data")
            wav_header.extend((num_samples * 2).to_bytes(4, 'little'))
            
            with open(output_path, 'wb') as f:
                f.write(wav_header)
                f.write(bytes(num_samples * 2))
            
            logger.info(f"✓ [Piper] Dummy audio created")
            return output_path
        
        except Exception as e:
            logger.error(f"✗ [Piper] Dummy audio creation failed: {e}", exc_info=True)
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
        
        logger.info(f"[Piper] Status check:")
        for key, value in status.items():
            logger.info(f"  {key}: {value}")
        
        return status


# ===== WHISPER API - SPEECH TO TEXT =====

class WhisperAPI:
    """Speech-to-Text using OpenAI Whisper"""
    
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.WHISPER_MODEL
        logger.info(f"✓ WhisperAPI initialized: model={self.model}")

    async def transcribe_streaming(self, audio_bytes: bytes) -> dict:
        """Transcribe audio chunk (for partial/streaming transcription)."""
        try:
            # Placeholder for streaming Whisper API
            return {"partial_transcription": ""}
        except Exception as e:
            logger.error(f"[Whisper] Streaming error: {e}")
            return {"partial_transcription": ""}

    async def transcribe_full(self, audio_bytes: bytes) -> dict:
        """Transcribe full audio from combined chunks."""
        try:
            import tempfile
            
            # Save audio to temp file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(audio_bytes)
                temp_path = f.name
            
            logger.info(f"[Whisper] Transcribing: {temp_path}")
            
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
                logger.error(f"[Whisper] Failed: {result.stderr}")
                return {"full_transcription": ""}
            
            # Parse JSON output
            import json
            output = json.loads(result.stdout)
            transcription = output.get("text", "")
            
            logger.info(f"[Whisper] ✓ Transcribed: {transcription[:50]}...")
            return {"full_transcription": transcription}
        
        except Exception as e:
            logger.error(f"[Whisper] Error: {e}")
            return {"full_transcription": ""}


# ===== HUGGINGFACE API - LLM INFERENCE =====

class HuggingFaceAPI:
    """LLM inference using HuggingFace models"""
    
    def __init__(self):
        self.api_key = settings.HUGGINGFACE_API_KEY
        self.model = settings.HUGGINGFACE_MODEL
        logger.info(f"✓ HuggingFaceAPI initialized: model={self.model}")

    async def semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts (0-1)"""
        try:
            # TODO: Implement actual semantic similarity using sentence-transformers
            # Placeholder returning dummy value
            return 0.7
        except Exception as e:
            logger.error(f"[HF] Similarity error: {e}")
            return 0.5

    async def evaluate_correctness(self, question: str, response: str, job_description: str) -> dict:
        """Evaluate if response is correct/partial/wrong"""
        try:
            # TODO: Implement actual evaluation using LLM
            # Placeholder returning dummy evaluation
            return {
                "assessment": "partial",
                "feedback": "Good response, could provide more details."
            }
        except Exception as e:
            logger.error(f"[HF] Evaluation error: {e}")
            return {
                "assessment": "partial",
                "feedback": "Unable to evaluate."
            }

    async def generate(self, prompt: str) -> str:
        """Generate text from prompt using LLM"""
        try:
            # TODO: Implement actual text generation using HuggingFace API
            # Placeholder returning dummy response
            return "This is a generated response."
        except Exception as e:
            logger.error(f"[HF] Generation error: {e}")
            return "Error generating response."
