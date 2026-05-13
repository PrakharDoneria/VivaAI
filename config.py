import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")

    # Optional. When set, state-changing API routes require matching X-API-Key header.
    # Use a value distinct from SECRET_KEY; never commit real keys.
    VIVAAI_API_KEY = os.environ.get("VIVAAI_API_KEY", "").strip()

    SARVAM_API_KEY = os.environ.get("SARVAM_API_KEY", "")
    SARVAM_CHAT_MODEL = os.environ.get("SARVAM_CHAT_MODEL", "sarvam-m")
    SARVAM_STT_MODEL = os.environ.get("SARVAM_STT_MODEL", "saarika:v2.5")
    SARVAM_STT_LANGUAGE = os.environ.get("SARVAM_STT_LANGUAGE", "en-IN")
    SARVAM_STT_CODEC = os.environ.get("SARVAM_STT_CODEC", "webm")

    DEBUG = os.environ.get("DEBUG", "True").lower() in ("true", "1", "yes")

    HOST = os.environ.get("HOST", "0.0.0.0")
    PORT = int(os.environ.get("PORT", 5000))

    INTERVIEW_DURATION_MINUTES = int(os.environ.get("INTERVIEW_DURATION_MINUTES", 10))
    MAX_QUESTIONS = int(os.environ.get("MAX_QUESTIONS") or 6)

    AUDIO_FOLDER = "static/audio/questions"
    ANSWERS_FOLDER = "static/audio/answers"

    DATABASE_PATH = "database/vivaai.db"

    STUN_SERVER = "stun:stun.l.google.com:19302"