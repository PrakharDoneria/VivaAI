import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "vivaai-secret")

    SARVAM_API_KEY = os.environ.get("SARVAM_API_KEY", "")
    SARVAM_CHAT_MODEL = os.environ.get("SARVAM_CHAT_MODEL", "sarvam-m")
    SARVAM_STT_MODEL = os.environ.get("SARVAM_STT_MODEL", "saarika:v2.5")
    SARVAM_STT_LANGUAGE = os.environ.get("SARVAM_STT_LANGUAGE", "en-IN")
    SARVAM_STT_CODEC = os.environ.get("SARVAM_STT_CODEC", "webm")

    AI_PROVIDER = os.environ.get("AI_PROVIDER", "sarvam")
    AI_TEMPERATURE = float(os.environ.get("AI_TEMPERATURE", "0.7"))

    DEBUG = os.environ.get("DEBUG", "True").lower() in ("true", "1", "yes")
    ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")

    HOST = os.environ.get("HOST", "0.0.0.0")
    PORT = int(os.environ.get("PORT", 5000))

    INTERVIEW_DURATION_MINUTES = int(os.environ.get("INTERVIEW_DURATION_MINUTES", 10))
    MAX_QUESTIONS = int(os.environ.get("MAX_QUESTIONS", 6))

    AUDIO_FOLDER = os.environ.get("AUDIO_FOLDER", "static/audio/questions")
    ANSWERS_FOLDER = os.environ.get("ANSWERS_FOLDER", "static/audio/answers")

    DATABASE_PATH = os.environ.get("DATABASE_PATH", "database/vivaai.db")
    STUN_SERVER = os.environ.get("STUN_SERVER", "stun:stun.l.google.com:19302")

    CORS_ALLOWED_ORIGINS = os.environ.get("CORS_ALLOWED_ORIGINS", "*")
    RATE_LIMIT_WINDOW_SECONDS = int(os.environ.get("RATE_LIMIT_WINDOW_SECONDS", "60"))
    RATE_LIMIT_AUTH_PER_WINDOW = int(os.environ.get("RATE_LIMIT_AUTH_PER_WINDOW", "10"))
    RATE_LIMIT_AI_PER_WINDOW = int(os.environ.get("RATE_LIMIT_AI_PER_WINDOW", "30"))


REQUIRED_ENV_VARS = ["SECRET_KEY"]


def validate_config() -> None:
    """Validate startup configuration and fail fast on invalid required settings."""
    missing = [key for key in REQUIRED_ENV_VARS if not os.environ.get(key)]
    if missing:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(sorted(missing))}."
        )

    allowed_envs = {"development", "staging", "production"}
    if Config.ENVIRONMENT not in allowed_envs:
        raise RuntimeError(
            f"ENVIRONMENT must be one of {sorted(allowed_envs)}, got '{Config.ENVIRONMENT}'."
        )
