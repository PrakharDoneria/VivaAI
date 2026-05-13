from flask import Blueprint, request, jsonify, current_app
from ai.question_engine import generate_question
from ai.tts_engine import generate_voice
from ai.report_engine import generate_report
from ai.stt_engine import transcribe_audio
from models.interview import save_report
from utils.sanitization import sanitize_model_output
from utils.validation import QuestionRequest, ReportRequest
from pydantic import ValidationError
import threading
import json
from extensions import db

ai_bp = Blueprint("ai", __name__)


@ai_bp.route("/api/ai/question", methods=["POST"])
def question():
    try:
        data = QuestionRequest(**request.get_json())
    except (ValidationError, TypeError) as e:
        return jsonify({"error": "Invalid input", "details": str(e)}), 400

    role = data.role
    answer = data.answer
    question_history = data.question_history

    try:
        question_text = sanitize_model_output(generate_question(role, answer, question_history))
        audio_url = generate_voice(question_text)

        return jsonify({
            "question": question_text,
            "audio": audio_url
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@ai_bp.route("/api/ai/report", methods=["POST"])
def report():
    try:
        data = ReportRequest(**request.get_json())
    except (ValidationError, TypeError) as e:
        return jsonify({"error": "Invalid input", "details": str(e)}), 400

    role = data.role
    qa_history = data.qa_history
    room_id = data.room_id

    def generate_and_save_report(app_context, room_id, role, qa_history):
        with app_context:
            try:
                report_text = sanitize_model_output(generate_report(role, qa_history))
                save_report(room_id, report_text, json.dumps(qa_history))
                print(f"  [AI] Report generated for room: {room_id}")
            except Exception as e:
                print(f"  [AI Error] Background report generation failed: {str(e)}")

    from flask import current_app
    app_context = current_app.app_context()
    
    # Start background task
    thread = threading.Thread(
        target=generate_and_save_report,
        args=(app_context, room_id, role, qa_history)
    )
    thread.start()

    return jsonify({"status": "processing", "message": "Report is being generated in the background."})


@ai_bp.route("/api/ai/transcribe", methods=["POST"])
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