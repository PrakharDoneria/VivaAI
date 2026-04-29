from flask import Blueprint, request, jsonify
from pydantic import ValidationError

from ai.question_engine import generate_question
from ai.tts_engine import generate_voice
from ai.report_engine import generate_report
from ai.stt_engine import transcribe_audio
from config import Config
from models.interview import save_report
from utils.rate_limit import rate_limiter
from utils.sanitization import sanitize_model_output
from utils.validation import QuestionRequest, ReportRequest

ai_bp = Blueprint("ai", __name__)


def _is_rate_limited(scope: str) -> bool:
    key = f"{scope}:{request.remote_addr or 'unknown'}"
    return not rate_limiter.allow(
        key,
        Config.RATE_LIMIT_AI_PER_WINDOW,
        Config.RATE_LIMIT_WINDOW_SECONDS,
    )


@ai_bp.route("/api/ai/question", methods=["POST"])
def question():
    """Generate a follow-up interview question and optional TTS audio URL."""
    if _is_rate_limited("question"):
        return jsonify({"error": "Rate limit exceeded"}), 429

    payload = request.get_json(silent=True) or {}
    try:
        data = QuestionRequest(**payload)
    except (ValidationError, TypeError) as error:
        return jsonify({"error": "Invalid input", "details": str(error)}), 400

    try:
        question_text = sanitize_model_output(
            generate_question(data.role, data.answer, data.question_history)
        )
        audio_url = generate_voice(question_text)
        return jsonify({"question": question_text, "audio": audio_url})
    except Exception as error:
        return jsonify({"error": str(error)}), 500


@ai_bp.route("/api/ai/report", methods=["POST"])
def report():
    """Generate final interview report and persist it when room_id is available."""
    if _is_rate_limited("report"):
        return jsonify({"error": "Rate limit exceeded"}), 429

    payload = request.get_json(silent=True) or {}
    try:
        data = ReportRequest(**payload)
    except (ValidationError, TypeError) as error:
        return jsonify({"error": "Invalid input", "details": str(error)}), 400

    try:
        report_text = sanitize_model_output(generate_report(data.role, data.qa_history))
        if data.room_id:
            import json

            save_report(data.room_id, report_text, json.dumps(data.qa_history))
        return jsonify({"report": report_text})
    except Exception as error:
        return jsonify({"error": str(error)}), 500


@ai_bp.route("/api/ai/transcribe", methods=["POST"])
def transcribe():
    """Transcribe uploaded audio response into plain text."""
    if _is_rate_limited("transcribe"):
        return jsonify({"error": "Rate limit exceeded"}), 429

    file = request.files.get("audio")
    if not file:
        return jsonify({"error": "Missing audio file"}), 400

    try:
        audio_bytes = file.read()
        if not audio_bytes:
            return jsonify({"error": "Empty audio file"}), 400

        transcript = transcribe_audio(
            audio_bytes,
            filename=file.filename or "answer.webm",
            content_type=file.content_type or "audio/webm",
        )
        return jsonify({"transcript": sanitize_model_output(transcript)})
    except Exception as error:
        return jsonify({"error": str(error)}), 500
