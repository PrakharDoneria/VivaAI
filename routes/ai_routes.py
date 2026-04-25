from flask import Blueprint, request, jsonify, g
from ai.question_engine import generate_question
from ai.tts_engine import generate_voice
from ai.report_engine import generate_report
from ai.stt_engine import transcribe_audio
from models.interview import save_report
from utils.sanitization import sanitize_model_output
from utils.validation import QuestionRequest, ReportRequest
from utils.auth import require_room_token
from pydantic import ValidationError

ai_bp = Blueprint("ai", __name__)


@ai_bp.route("/api/ai/question", methods=["POST"])
@require_room_token
def question():
    try:
        data = QuestionRequest(**request.get_json())
    except (ValidationError, TypeError) as e:
        return jsonify({"error": "Invalid input", "details": str(e)}), 400

    try:
        question_text = sanitize_model_output(
            generate_question(data.role, data.answer, data.question_history)
        )
        audio_url = generate_voice(question_text)

        return jsonify({"question": question_text, "audio": audio_url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@ai_bp.route("/api/ai/report", methods=["POST"])
@require_room_token
def report():
    try:
        data = ReportRequest(**request.get_json())
    except (ValidationError, TypeError) as e:
        return jsonify({"error": "Invalid input", "details": str(e)}), 400

    try:
        report_text = sanitize_model_output(generate_report(data.role, data.qa_history))

        if data.room_id:
            import json
            save_report(data.room_id, report_text, json.dumps(data.qa_history))

        return jsonify({"report": report_text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@ai_bp.route("/api/ai/transcribe", methods=["POST"])
@require_room_token
def transcribe():
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
    except Exception as e:
        return jsonify({"error": str(e)}), 500
