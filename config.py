import os
from dotenv import load_dotenv

load_dotenv()


def _env(name, default=None, cast=str):
    value = os.getenv(name, default)
    if value is None:
        return None
    if cast is bool:
        return str(value).lower() in ("true", "1", "yes")
    return cast(value)


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "vivaai-secret")

    # Optional. When set, state-changing API routes require matching X-API-Key header.
    # Use a value distinct from SECRET_KEY; never commit real keys.
    VIVAAI_API_KEY = os.environ.get("VIVAAI_API_KEY", "").strip()

    SARVAM_API_KEY = os.environ.get("SARVAM_API_KEY", "")
    SARVAM_CHAT_MODEL = os.environ.get("SARVAM_CHAT_MODEL", "sarvam-m")
    SARVAM_STT_MODEL = os.environ.get("SARVAM_STT_MODEL", "saarika:v2.5")
    SARVAM_STT_LANGUAGE = os.environ.get("SARVAM_STT_LANGUAGE", "en-IN")
    SARVAM_STT_CODEC = os.environ.get("SARVAM_STT_CODEC", "webm")

    DEBUG = _env("DEBUG", True, bool)

    HOST = _env("HOST", "0.0.0.0")
    PORT = _env("PORT", 5000, int)

    INTERVIEW_DURATION_MINUTES = _env("INTERVIEW_DURATION_MINUTES", 10, int)
    MAX_QUESTIONS = _env("MAX_QUESTIONS", 6, int)

    AUDIO_FOLDER = "static/audio/questions"
    ANSWERS_FOLDER = "static/audio/answers"

    DATABASE_PATH = "database/vivaai.db"

    STUN_SERVER = "stun:stun.l.google.com:19302"