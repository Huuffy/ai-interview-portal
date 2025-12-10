# backend/config.py
# Configuration & Settings

import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # ===== API =====
    API_TITLE = "AI Interview Portal"
    API_VERSION = "1.0.0"
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    DEBUG = os.getenv("DEBUG", "False") == "True"
    
    # ===== INTERVIEW =====
    INTERVIEW_DURATION_MINUTES = int(os.getenv("INTERVIEW_DURATION_MINUTES", "5"))
    CLOSING_BUFFER_SECONDS = 90
    MIN_QUESTIONS = 3
    MAX_QUESTIONS = 8
    QUESTION_TIMEOUT_SECONDS = 60
    
    # ===== AUDIO =====
    VAD_SILENCE_THRESHOLD_MS = 500
    AUDIO_CHUNK_SIZE_MS = 20
    SAMPLE_RATE = 16000
    
    # ===== LLM (HuggingFace) =====
    LLM_MODEL = "mistralai/Mistral-7B-Instruct-v0.2"
    LLM_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")
    LLM_TIMEOUT = 30
    
    # ===== TTS (Piper) =====
    TTS_ENGINE = "piper"
    TTS_VOICE = "en_US-male"
    
    # ===== MuseTalk =====
    MUSETALK_GPU = True
    MUSETALK_FP16 = True
    
    # ===== Database =====
    DATABASE_URL = "sqlite:///./data/interview.db"
    
    # ===== Media Storage =====
    MEDIA_DIR = "media"
    VIDEO_CACHE_DIR = "media/videos"
    AUDIO_CACHE_DIR = "media/audio"
    AVATAR_DIR = "media/avatars"
    
    # ===== WebSocket =====
    WS_HEARTBEAT = 30
    WS_TIMEOUT = 300
    
    # ===== CORS =====
    ALLOWED_ORIGINS = [
        "http://localhost:5173",
        os.getenv("FRONTEND_URL", "http://localhost:5173"),
        "*.vercel.app"
    ]
    
    # ===== External APIs =====
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

settings = Settings()
