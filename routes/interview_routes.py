import re
import uuid

from flask import Blueprint, request, jsonify, render_template
from pydantic import ValidationError

from config import Config
from models.interview import create_interview, save_answers, get_interview
from utils.rate_limit import rate_limiter
from utils.validation import CreateInterviewRequest, SaveAnswersRequest

interview_bp = Blueprint("interview", __name__)


def validate_room_id(room_id):
    """Validate room IDs to reduce abuse and malformed route values."""
    return bool(room_id and re.match(r"^[A-Z0-9-]{1,50}$", room_id, re.I))


def _auth_scope_limited(scope: str) -> bool:
    key = f"{scope}:{request.remote_addr or 'unknown'}"
    return not rate_limiter.allow(
        key,
        Config.RATE_LIMIT_AUTH_PER_WINDOW,
        Config.RATE_LIMIT_WINDOW_SECONDS,
    )


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
def create():
    if _auth_scope_limited("create_interview"):
        return jsonify({"error": "Rate limit exceeded"}), 429

    payload = request.get_json(silent=True) or {}
    try:
        data = CreateInterviewRequest(**payload)
    except (ValidationError, TypeError) as error:
        return jsonify({"error": "Invalid input", "details": str(error)}), 400

    room_id = data.room_id or str(uuid.uuid4())[:8]

    try:
        create_interview(room_id, data.role, data.candidate_name)
        return jsonify({"status": "created", "room_id": room_id})
    except Exception as error:
        return jsonify({"error": str(error)}), 500


@interview_bp.route("/api/interview/<room_id>", methods=["GET"])
def get(room_id):
    if not validate_room_id(room_id):
        return jsonify({"error": "Invalid room ID"}), 400

    interview = get_interview(room_id)
    return (jsonify(dict(interview)), 200) if interview else (jsonify({"error": "Interview not found"}), 404)


@interview_bp.route("/api/interview/<room_id>/answers", methods=["POST"])
def save(room_id):
    if not validate_room_id(room_id):
        return jsonify({"error": "Invalid room ID"}), 400

    payload = request.get_json(silent=True) or {}
    try:
        data = SaveAnswersRequest(**payload)
    except (ValidationError, TypeError) as error:
        return jsonify({"error": "Invalid input", "details": str(error)}), 400

    try:
        save_answers(room_id, data.answers)
        return jsonify({"status": "answers_saved"})
    except Exception as error:
        return jsonify({"error": str(error)}), 500
