import asyncio
import subprocess
import os
from typing import Optional, List, Union
import logging
from pathlib import Path
import shutil
from config import settings
import tempfile 
import yaml
import re
from huggingface_hub import InferenceClient

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# ===== MUSETALK API - ACTUAL VIDEO GENERATION =====

class MuseVAPI:
    """Wrapper for MuseV to generate the base listening video (idle animation)."""
    
    def __init__(self):
        self.root = settings.MUSEV_ROOT
        self.python_bin = settings.MUSETALK_PYTHON_BIN # Usually shares env with MuseTalk
        self.gpu = settings.MUSETALK_GPU
        self.lock = asyncio.Lock()
        
        logger.info(f"✓ MuseV initialized: {self.root}")

    async def generate_base_video(self, image_path: str, output_path: str) -> Optional[str]:
        """
        Generate a 30-second idle video from a static image.
        """
        async with self.lock:
            if os.path.exists(output_path):
                logger.info(f"[MuseV] Base video already exists: {output_path}")
                return output_path

            logger.info(f"[MuseV] Generating new base video (This takes time!)...")
            
            try:
                # MuseV requires absolute paths
                root_abs = os.path.abspath(self.root)
                image_abs = os.path.abspath(image_path)
                output_abs = os.path.abspath(output_path)
                os.makedirs(os.path.dirname(output_abs), exist_ok=True)

                # Construct MuseV Command
                # NOTE: Adjust arguments based on your specific MuseV version/script
                cmd = [
                    self.python_bin,
                    "-m", "scripts.inference", # Or "inference.py" depending on repo structure
                    "--input_image", image_abs,
                    "--output_path", output_abs,
                    "--duration", "30", # Generate 30 seconds
                    "--gpu", str(self.gpu)
                ]

                # Environment setup
                env = os.environ.copy()
                env["PYTHONPATH"] = root_abs + os.pathsep + env.get("PYTHONPATH", "")

                logger.info(f"[MuseV] Running: {' '.join(cmd)}")
                
                # Run Inference
                result = await asyncio.to_thread(
                    subprocess.run,
                    cmd,
                    cwd=root_abs,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=1200 # Give it 20 mins, MuseV is heavy
                )

                if result.returncode != 0:
                    logger.error(f"[MuseV] Failed: {result.stderr[-1000:]}")
                    return None

                # MuseV often outputs to a folder, so we might need to find the specific mp4
                # Assuming output_abs is the exact file path for this example:
                if os.path.exists(output_abs):
                    logger.info(f"✓ [MuseV] Generated base video: {output_path}")
                    return output_path
                else:
                    logger.error(f"[MuseV] Output file not found after success code.")
                    return None

            except Exception as e:
                logger.error(f"[MuseV] Error: {e}", exc_info=True)
                return None


# [UPDATED] ===== MUSETALK API =====

class MuseTalkAPI:
    # ... __init__ remains same ...
    def __init__(self):
        self.musetalk_root = settings.MUSETALK_ROOT
        self.gpu = settings.MUSETALK_GPU
        self.fp16 = settings.MUSETALK_FP16
        self.python_bin = settings.MUSETALK_PYTHON_BIN
        self.inference_script = self._find_inference_script()
        self.lock = asyncio.Lock()
        
        logger.info(f"✓ MuseTalk initialized")

    # ... _find_inference_script and _get_ffmpeg_path remain same ...
    def _find_inference_script(self) -> Optional[str]:
        search_locations = [
            os.path.join(self.musetalk_root, "scripts", "inference.py"),
            os.path.join(self.musetalk_root, "inference.py"),
            os.path.abspath("inference.py")
        ]
        for path in search_locations:
            if os.path.exists(path): return os.path.abspath(path)
        return None

    def _get_ffmpeg_path(self):
        musetalk_abs = os.path.abspath(self.musetalk_root)
        ffmpeg_dir = os.path.join(musetalk_abs, "ffmpeg", "bin")
        ffmpeg_exe = os.path.join(ffmpeg_dir, "ffmpeg.exe")
        if os.path.exists(ffmpeg_exe): return ffmpeg_dir, ffmpeg_exe
        return None, None

    async def generate(
        self,
        input_source: str,  # CHANGED NAME: Can be Image (.png) OR Video (.mp4)
        audio_path: str,
        output_path: str
    ) -> Optional[str]:
        """
        Generate lip-synced video using MuseTalk.
        input_source: Path to 'base_listening.mp4' (video) OR 'avatar.png' (image)
        """
        async with self.lock:
            config_path = None
            try:
                # --- 0. RESOLVE PATHS ---
                musetalk_abs = os.path.abspath(self.musetalk_root)
                if not os.path.exists(input_source):
                    logger.error(f"[MuseTalk] Input source not found: {input_source}")
                    return None
                
                # FORCE FORWARD SLASHES
                input_abs = os.path.abspath(input_source).replace("\\", "/")
                audio_abs = os.path.abspath(audio_path).replace("\\", "/")
                output_abs = os.path.abspath(output_path).replace("\\", "/")
                
                # Filename variations for bbox_shift lookup
                input_basename = os.path.basename(input_abs)
                input_name_no_ext = os.path.splitext(input_basename)[0]

                # --- 1. SETUP FFMPEG ---
                ffmpeg_dir, ffmpeg_exe = self._get_ffmpeg_path()
                use_local_ffmpeg = True if ffmpeg_dir else False

                # --- 2. PREPARE MODEL PATHS ---
                unet_path = os.path.join(musetalk_abs, "models", "musetalkV15", "unet.pth")
                musetalk_json = os.path.join(musetalk_abs, "models", "musetalkV15", "musetalk.json")
                whisper_path = os.path.join(musetalk_abs, "models", "whisper")

                # --- 3. CREATE CONFIGURATION ---
                os.makedirs(os.path.dirname(output_abs), exist_ok=True)

                # [CRITICAL] Catch-all bbox_shift for both Image and Video inputs
                bbox_shift_config = {
                    input_abs: 0,
                    input_basename: 0,
                    input_name_no_ext: 0,
                    "video_path": 0 
                }

                config_payload = {
                    "task_type": "dubbing",
                    "video_path": input_abs, # MuseTalk accepts video path here for Dubbing
                    "audio_path": audio_abs,
                    "bbox_shift": bbox_shift_config, 
                    "video_out_path": output_abs,
                    "fp16": True,
                }

                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as tmp_config:
                    yaml.dump(config_payload, tmp_config, default_flow_style=False)
                    config_path = tmp_config.name

                logger.info(f"[MuseTalk] Generating video...")
                logger.info(f"  Input: {input_basename}")

                # --- 4. EXECUTE INFERENCE ---
                cmd = [
                    self.python_bin,
                    "-m", "scripts.inference",
                    "--inference_config", config_path.replace("\\", "/"), 
                    "--gpu", str(self.gpu),
                    "--unet_config", musetalk_json.replace("\\", "/"),
                    "--unet_model_path", unet_path.replace("\\", "/"),
                    "--whisper_dir", whisper_path.replace("\\", "/")
                ]

                env = os.environ.copy()
                env["PYTHONPATH"] = musetalk_abs + os.pathsep + env.get("PYTHONPATH", "")
                if use_local_ffmpeg:
                    env["PATH"] = ffmpeg_dir + os.pathsep + env.get("PATH", "")

                result = await asyncio.to_thread(
                    subprocess.run,
                    cmd,
                    cwd=musetalk_abs,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=600 
                )

                if result.returncode != 0:
                    logger.error(f"[MuseTalk] FAILED: {result.stderr[-1000:]}")
                    return None

                if not os.path.exists(output_abs):
                    logger.error(f"[MuseTalk] Output not found: {output_abs}")
                    return None

                logger.info(f"✓ [MuseTalk] Success: {output_path}")
                return output_path

            except Exception as e:
                logger.error(f"[MuseTalk] Error: {e}", exc_info=True)
                return None
            finally:
                if config_path and os.path.exists(config_path):
                    try: os.remove(config_path)
                    except: pass
    
    async def generate_listening_video(
        self,
        avatar_image: str,
        audio_duration_seconds: float,
        output_path: str
    ) -> Optional[str]:
        """
        Generate listening/nodding video (interviewer listening to candidate).
        """
        try:
            logger.info(f"[MuseTalk] Generating listening video...")
            
            silence_audio_path = os.path.join(
                os.path.dirname(output_path),
                "silence.wav"
            )
            
            await self._create_silent_audio(
                silence_audio_path,
                audio_duration_seconds
            )
            
            output = await self.generate(
                avatar_image=avatar_image,
                audio_path=silence_audio_path,
                output_path=output_path,
                video_type="standard"
            )
            
            if os.path.exists(silence_audio_path):
                os.remove(silence_audio_path)
            
            return output
        
        except Exception as e:
            logger.error(f"[MuseTalk] Listening video error: {e}", exc_info=True)
            return None
    
    async def _create_silent_audio(self, output_path: str, duration_seconds: float) -> bool:
        """Create a silent WAV audio file for listening animations."""
        try:
            sample_rate = 22050
            duration = int(duration_seconds)
            num_samples = sample_rate * duration
            
            # Minimal WAV header creation
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
            
            return True
        except Exception as e:
            logger.error(f"[Audio] Silent audio creation failed: {e}", exc_info=True)
            return False

# ===== PIPER TTS API - ACTUAL AUDIO GENERATION =====

class PiperTTS:
    """Text-to-Speech using Piper TTS"""
    
    def __init__(self):
        self.voice = settings.PIPER_VOICE
        self.speed = settings.PIPER_SPEED
        self.piper_bin = settings.PIPER_BIN
        os.makedirs(settings.AUDIO_CACHE_DIR, exist_ok=True)
    
    def _find_piper_executable(self) -> Optional[str]:
        if self.piper_bin and os.path.exists(self.piper_bin):
            return self.piper_bin
        
        try:
            cmd = ['where', 'piper'] if os.name == 'nt' else ['which', 'piper']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None
    
    async def synthesize(self, text: str, output_path: str) -> Optional[str]:
        try:
            clean_text = text.strip()
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            piper_bin = self._find_piper_executable()
            if not piper_bin:
                logger.error(f"✗ [Piper] Executable not found")
                return None
            
            cmd = [
                piper_bin,
                "--model", self.voice,
                "--output_file", output_path,
                "--length_scale", str(self.speed),
            ]
            
            result = await asyncio.to_thread(
                subprocess.run,
                cmd,
                input=clean_text,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0 or not os.path.exists(output_path):
                logger.error(f"✗ [Piper] FAILED (code {result.returncode})")
                return None
            
            return output_path
        except Exception as e:
            logger.error(f"✗ [Piper] EXCEPTION: {e}", exc_info=True)
            return None

# ===== WHISPER API - SPEECH TO TEXT =====

class WhisperAPI:
    """Speech-to-Text using OpenAI Whisper Python Library (No Subprocess)"""
    
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model_name = settings.WHISPER_MODEL
        self.model = None
        
        # Inject FFmpeg path once during init
        self._inject_ffmpeg()
        logger.info(f"✓ WhisperAPI initialized: model={self.model_name}")

    def _inject_ffmpeg(self):
        """Inject local FFmpeg into PATH"""
        ffmpeg_path = os.path.join(settings.MUSETALK_ROOT, "ffmpeg", "bin")
        if os.path.exists(ffmpeg_path):
            logger.info(f"[Whisper] Injecting local FFmpeg into PATH: {ffmpeg_path}")
            os.environ["PATH"] = ffmpeg_path + os.pathsep + os.environ["PATH"]

    def _load_model(self):
        """Lazy load model to avoid locking startup"""
        if self.model is None:
            import whisper
            logger.info(f"[Whisper] Loading model '{self.model_name}' into memory...")
            self.model = whisper.load_model(self.model_name)
    
    async def transcribe_full(self, audio_bytes: bytes) -> dict:
        """Transcribe audio bytes using Whisper Python API"""
        import tempfile
        import whisper
        temp_path = None
        
        try:
            # Load model if not ready (runs in thread to avoid blocking)
            if self.model is None:
                await asyncio.to_thread(self._load_model)

            # Save audio to temp file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(audio_bytes)
                temp_path = f.name
            
            logger.info(f"[Whisper] Transcribing file...")
            
            # Run transcription in thread
            def _run_transcribe():
                return self.model.transcribe(temp_path, fp16=False) 
            
            result = await asyncio.to_thread(_run_transcribe)
            text = result["text"].strip()
            
            logger.info(f"✓ [Whisper] Transcribed: {text[:100]}...")
            return {"full_transcription": text}
        
        except Exception as e:
            logger.error(f"[Whisper] Error: {e}", exc_info=True)
            return {"full_transcription": ""}
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except:
                    pass

# ===== HUGGINGFACE API - LLM INFERENCE =====

class HuggingFaceAPI:
    """LLM inference using HuggingFace models"""
    
    def __init__(self):
        self.api_key = settings.HUGGINGFACE_API_KEY
        # CHANGED: Use Mistral Instruct v0.2 which supports text-generation better on free tier
        self.model = "mistralai/Mistral-7B-Instruct-v0.2" 
        self.client = InferenceClient(token=self.api_key)
        logger.info(f"✓ HuggingFaceAPI initialized: model={self.model}")
    
    async def generate(self, job_description: str) -> Union[str, list]:
        """
        Generate 5 interview questions based on job description.
        """
        try:
            logger.info(f"[HF] Generating interview questions via API...")
            
            # Mistral Instruct Format
            prompt = f"<s>[INST] You are an expert technical interviewer. Generate exactly 5 distinct technical interview questions for a candidate applying for this role: '{job_description}'. Return ONLY the questions as a numbered list. [/INST]"
            
            response = await asyncio.to_thread(
                self.client.text_generation,
                prompt,
                model=self.model,
                max_new_tokens=512,
                temperature=0.7,
                return_full_text=False
            )
            
            # Parse and clean
            raw_text = response.strip()
            lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
            
            cleaned_questions = []
            for line in lines:
                # Remove numbers and dots (e.g. "1. Question" -> "Question")
                clean = re.sub(r'^\d+[\.\)\-]\s*', '', line)
                if clean and len(clean) > 10: # Filter out short garbage
                    cleaned_questions.append(clean)
            
            final_list = cleaned_questions[:5]
            
            if not final_list:
                 raise Exception("No questions generated")

            logger.info(f"✓ [HF] Generated {len(final_list)} questions")
            return "\n".join(final_list)
        
        except Exception as e:
            logger.error(f"[HF] Question generation error: {e}")
            # Fallback if API fails
            return "Tell me about yourself.\nWhat are your strengths?\nDescribe a challenge you faced.\nWhy do you want this job?\nAny questions for us?"
    
    async def evaluate_response(self, question: str, response: str, job_description: str) -> dict:
        """Evaluate candidate response using LLM."""
        try:
            logger.info(f"[HF] Evaluating response...")
            
            if len(response.strip()) < 5:
                return {"score": 2, "marks": "2/10", "feedback": "Response too short."}

            prompt = f"<s>[INST] Evaluate this interview answer.\nRole: {job_description}\nQuestion: {question}\nAnswer: {response}\n\nOutput STRICTLY in this format:\nSCORE: [1-10]\nFEEDBACK: [One sentence feedback] [/INST]"
            
            output = await asyncio.to_thread(
                self.client.text_generation,
                prompt,
                model=self.model,
                max_new_tokens=150,
                temperature=0.3
            )
            
            text = output.strip()
            score = 5
            feedback = "Good attempt."
            
            # Robust parsing
            score_match = re.search(r'SCORE:\s*(\d+)', text, re.IGNORECASE)
            if score_match:
                score = int(score_match.group(1))
                
            feedback_match = re.search(r'FEEDBACK:\s*(.*)', text, re.IGNORECASE)
            if feedback_match:
                feedback = feedback_match.group(1).strip()
            
            return {
                "score": score,
                "marks": f"{score}/10",
                "feedback": feedback
            }
        
        except Exception as e:
            logger.error(f"[HF] Evaluation error: {e}")
            return {"score": 5, "marks": "5/10", "feedback": "Evaluation unavailable."}