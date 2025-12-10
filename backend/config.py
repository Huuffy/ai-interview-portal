import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # API Configuration
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = os.getenv("API_PORT", "8000")
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    
    # Interview Configuration
    INTERVIEW_DURATION_MINUTES = int(os.getenv("INTERVIEW_DURATION_MINUTES", "5"))
    CLOSING_BUFFER_SECONDS = int(os.getenv("CLOSING_BUFFER_SECONDS", "30"))
    
    # Media Paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    MEDIA_DIR = os.getenv("MEDIA_DIR", os.path.join(BASE_DIR, "media"))
    AUDIO_CACHE_DIR = os.getenv("AUDIO_CACHE_DIR", os.path.join(MEDIA_DIR, "audio"))
    VIDEO_CACHE_DIR = os.getenv("VIDEO_CACHE_DIR", os.path.join(MEDIA_DIR, "video"))
    AVATAR_DIR = os.getenv("AVATAR_DIR", os.path.join(MEDIA_DIR, "avatars"))
    
    # MuseTalk Configuration
    MUSETALK_ROOT = os.getenv("MUSETALK_ROOT", os.path.join(BASE_DIR, "MuseTalk"))
    MUSETALK_GPU = int(os.getenv("MUSETALK_GPU", "0"))
    MUSETALK_FP16 = os.getenv("MUSETALK_FP16", "true").lower() == "true"
    MUSETALK_PYTHON_BIN = os.getenv("MUSETALK_PYTHON_BIN", "python")
    
    # Piper TTS Configuration
    PIPER_VOICE = os.getenv("PIPER_VOICE", "en_US-lessac-medium")
    PIPER_SPEED = float(os.getenv("PIPER_SPEED", "1.0"))
    
    # OpenAI Whisper Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
    
    # HuggingFace Configuration
    HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")
    HUGGINGFACE_MODEL = os.getenv("HUGGINGFACE_MODEL", "mistral-7b-instruct")

settings = Settings()
