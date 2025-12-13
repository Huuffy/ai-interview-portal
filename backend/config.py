import os
import sys
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # API Configuration
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = os.getenv("API_PORT", "8000")
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    
    # Interview Configuration
    DEFAULT_QUESTION_COUNT = int(os.getenv("DEFAULT_QUESTION_COUNT", "5"))
    CLOSING_BUFFER_SECONDS = int(os.getenv("CLOSING_BUFFER_SECONDS", "30"))
    
    # Media Paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    MEDIA_DIR = os.getenv("MEDIA_DIR", os.path.join(BASE_DIR, "media"))
    AUDIO_CACHE_DIR = os.getenv("AUDIO_CACHE_DIR", os.path.join(MEDIA_DIR, "audio"))
    VIDEO_CACHE_DIR = os.getenv("VIDEO_CACHE_DIR", os.path.join(MEDIA_DIR, "video"))
    AVATAR_DIR = os.getenv("AVATAR_DIR", os.path.join(MEDIA_DIR, "avatars"))

    # Ensure directories exist on startup
    os.makedirs(MEDIA_DIR, exist_ok=True)
    os.makedirs(VIDEO_CACHE_DIR, exist_ok=True)
    os.makedirs(AUDIO_CACHE_DIR, exist_ok=True)
    os.makedirs(AVATAR_DIR, exist_ok=True)
    
    # MuseTalk Configuration
    MUSETALK_ROOT = os.getenv("MUSETALK_ROOT", os.path.join(BASE_DIR, "MuseTalk"))
    MUSETALK_GPU = int(os.getenv("MUSETALK_GPU", "0"))
    MUSETALK_FP16 = os.getenv("MUSETALK_FP16", "true").lower() == "true"
    MUSETALK_PYTHON_BIN = os.getenv("MUSETALK_PYTHON_BIN", sys.executable)

    MUSEV_ROOT = os.getenv("MUSEV_ROOT", os.path.join(BASE_DIR, "MuseV"))
    # Base video filename to store/reuse
    BASE_VIDEO_NAME = "base_listening_loop.mp4"
    
    # Piper TTS Configuration
    PIPER_VOICE = os.getenv("PIPER_VOICE","en_US-bryce-medium")
    PIPER_SPEED = float(os.getenv("PIPER_SPEED", "1.0"))
    # Windows: Full path to piper executable (e.g., C:\Program Files\piper\piper.exe)
    # Linux/Mac: Just "piper" if installed globally
    PIPER_BIN = os.getenv("PIPER_BIN", os.path.join(BASE_DIR, "venv", "Scripts", "piper.exe")
)
    
    # OpenAI Whisper Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
    
    # HuggingFace Configuration
    HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")
    HUGGINGFACE_MODEL = os.getenv("HUGGINGFACE_MODEL", "mistral-7b-instruct")
    
    #Mount frontend
    FRONTEND_DIR = os.path.join(BASE_DIR, "frontend", "dist")

settings = Settings()
