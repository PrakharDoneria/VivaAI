from flask import Blueprint, request, jsonify, render_template
from models.interview import create_interview, save_answers, get_interview
from utils.validation import CreateInterviewRequest, SaveAnswersRequest
from pydantic import ValidationError
from middleware.auth import login_required
import uuid
import re
import secrets

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
@login_required
def create(current_user):
    try:
        data = CreateInterviewRequest(**request.get_json())
    except (ValidationError, TypeError) as e:
        return jsonify({"error": "Invalid input", "details": str(e)}), 400

    # Generate longer room ID for better security
    room_id = data.room_id or secrets.token_urlsafe(12)[:16]
    role = data.role
    candidate_name = data.candidate_name
    duration = data.duration

    try:
        create_interview(room_id, role, candidate_name, duration, current_user['id'])
        return jsonify({"status": "created", "room_id": room_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@interview_bp.route("/api/interview/<room_id>", methods=["GET"])
def get(room_id):
    if not validate_room_id(room_id):
        return jsonify({"error": "Invalid room ID"}), 400

    interview = get_interview(room_id)

    if interview:
        return jsonify(dict(interview))

    return jsonify({"error": "Interview not found"}), 404


@interview_bp.route("/api/interview/<room_id>/answers", methods=["POST"])
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