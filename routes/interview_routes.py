from flask import Blueprint, request, jsonify, render_template
from models.interview import create_interview, save_answers, get_interview
from utils.auth import require_api_key
from utils.validation import CreateInterviewRequest, SaveAnswersRequest
from pydantic import ValidationError
import uuid
import re
from pypdf import PdfReader
import io

interview_bp = Blueprint("interview", __name__)

def validate_room_id(room_id):
    if not room_id or not re.match(r"^[A-Z0-9-]{1,50}$", room_id, re.I):
        return False
    return True


@interview_bp.route("/interview/create", methods=["GET"])
def create_page():
    return render_template("index.html")


@interview_bp.route("/interview/<room_id>")
def room_page(room_id):
    if not validate_room_id(room_id):
        return render_template("index.html")

    interview = get_interview(room_id)
    if not interview:
        return render_template("index.html")
    return render_template("interview_room.html", room_id=room_id, interview=dict(interview))


@interview_bp.route("/api/interview/create", methods=["POST"])
@require_api_key
def create():
    try:
        data = CreateInterviewRequest(**request.get_json())
    except (ValidationError, TypeError) as e:
        return jsonify({"error": "Invalid input", "details": str(e)}), 400

    room_id = data.room_id or str(uuid.uuid4())[:8]
    role = data.role
    candidate_name = data.candidate_name
    duration = data.duration
    language = data.language
    resume_text = data.resume_text

    try:
        # Note: We are assuming create_interview is updated or we store these in session
        from flask import session
        session[f"resume_{room_id}"] = resume_text
        session[f"lang_{room_id}"] = language
        
        create_interview(room_id, role, candidate_name, duration)
        return jsonify({"status": "created", "room_id": room_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@interview_bp.route("/api/interview/upload-resume", methods=["POST"])
def upload_resume():
    if 'resume' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['resume']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file and file.filename.endswith('.pdf'):
        try:
            reader = PdfReader(io.BytesIO(file.read()))
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            
            return jsonify({"status": "success", "text": text[:4000]})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    return jsonify({"error": "Invalid file format. Please upload a PDF."}), 400


@interview_bp.route("/api/interview/<room_id>", methods=["GET"])
def get(room_id):
    if not validate_room_id(room_id):
        return jsonify({"error": "Invalid room ID"}), 400

    interview = get_interview(room_id)

    if interview:
        return jsonify(dict(interview))

    return jsonify({"error": "Interview not found"}), 404


@interview_bp.route("/api/interview/<room_id>/answers", methods=["POST"])
@require_api_key
def save(room_id):
    if not validate_room_id(room_id):
        return jsonify({"error": "Invalid room ID"}), 400

    try:
        data = SaveAnswersRequest(**request.get_json())
    except (ValidationError, TypeError) as e:
        return jsonify({"error": "Invalid input", "details": str(e)}), 400

    answers = data.answers

    try:
        save_answers(room_id, answers)
        return jsonify({"status": "answers_saved"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500