import json

from flask import Blueprint, request, jsonify
from ai.question_engine import generate_question
from ai.tts_engine import generate_voice
from ai.report_engine import generate_report
from ai.stt_engine import transcribe_audio
from limiter_ext import limiter
from models.interview import save_report
from utils.auth import require_api_key
from utils.sanitization import sanitize_model_output
from utils.validation import QuestionRequest, ReportRequest
from pydantic import ValidationError

ai_bp = Blueprint("ai", __name__)


def error_response(message, status=500, details=None):
    payload = {"error": message}
    if details:
        payload["details"] = details
    return jsonify(payload), status


def validate_request(schema):
    try:
        return schema(**request.get_json()), None
    except (ValidationError, TypeError) as exc:
        return None, error_response("Invalid input", 400, str(exc))


def sanitize(text):
    return sanitize_model_output(text)


@ai_bp.route("/api/ai/question", methods=["POST"])
@limiter.limit("10 per minute")
@require_api_key
def question():
    data, error = validate_request(QuestionRequest)
    if error:
        return error

    try:
        question_text = sanitize(generate_question(data.role, data.answer, data.question_history))
        audio_url = generate_voice(question_text)
        return jsonify(question=question_text, audio=audio_url)
    except Exception as exc:
        return error_response(str(exc))


@ai_bp.route("/api/ai/report", methods=["POST"])
@limiter.limit("10 per minute")
@require_api_key
def report():
    data, error = validate_request(ReportRequest)
    if error:
        return error

    try:
        report_text = sanitize(generate_report(data.role, data.qa_history))
        if data.room_id:
            save_report(data.room_id, report_text, json.dumps(data.qa_history))
        return jsonify(report=report_text)
    except Exception as exc:
        return error_response(str(exc))


@ai_bp.route("/api/ai/transcribe", methods=["POST"])
@limiter.limit("10 per minute")
@require_api_key
def transcribe():
    file = request.files.get("audio")
    if not file:
        return error_response("Missing audio file", 400)

    try:
        audio_bytes = file.read()
        if not audio_bytes:
            return error_response("Empty audio file", 400)

        transcript = transcribe_audio(
            audio_bytes,
            filename=file.filename or "answer.webm",
            content_type=file.content_type or "audio/webm",
        )
        return jsonify(transcript=sanitize(transcript))
    except Exception as exc:
        return error_response(str(exc))
