import re
import uuid

from flask import Blueprint, request, jsonify, render_template

from models.interview import create_interview, save_answers, get_interview

interview_bp = Blueprint("interview", __name__)

ROOM_ID_PATTERN = re.compile(r"^[A-Z0-9_-]{4,16}$")
MAX_NAME_LENGTH = 80
MAX_ROLE_LENGTH = 80
MAX_ANSWERS_LENGTH = 10000


def _require_json_object():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None, (jsonify({"error": "Request body must be valid JSON"}), 400)
    return data, None


def _sanitize_text(value):
    # Remove control characters while preserving user-visible text.
    return re.sub(r"[\x00-\x1F\x7F]", "", value).strip()


def _validate_required_string(data, field_name, max_length):
    value = data.get(field_name)

    if value is None:
        return None, f"'{field_name}' is required"
    if not isinstance(value, str):
        return None, f"'{field_name}' must be a string"

    cleaned = _sanitize_text(value)
    if not cleaned:
        return None, f"'{field_name}' cannot be empty"
    if len(cleaned) > max_length:
        return None, f"'{field_name}' must be <= {max_length} characters"

    return cleaned, None


@interview_bp.route("/interview/create", methods=["GET"])
def create_page():
    return render_template("index.html")


@interview_bp.route("/interview/<room_id>")
def room_page(room_id):
    interview = get_interview(room_id)
    if not interview:
        return render_template("index.html")
    return render_template("interview_room.html", room_id=room_id, interview=dict(interview))


@interview_bp.route("/api/interview/create", methods=["POST"])
def create():
    data, error = _require_json_object()
    if error:
        return error

    raw_room_id = data.get("room_id")
    if raw_room_id is None or raw_room_id == "":
        room_id = str(uuid.uuid4())[:8].upper()
    else:
        if not isinstance(raw_room_id, str):
            return jsonify({"error": "'room_id' must be a string"}), 400
        room_id = _sanitize_text(raw_room_id).upper()
        if not ROOM_ID_PATTERN.fullmatch(room_id):
            return jsonify({"error": "'room_id' must be 4-16 chars (A-Z, 0-9, _, -)"}), 400

    candidate_name, candidate_name_error = _validate_required_string(
        data, "candidate_name", MAX_NAME_LENGTH
    )
    if candidate_name_error:
        return jsonify({"error": candidate_name_error}), 400

    role_value = data.get("role", "Software Developer")
    if not isinstance(role_value, str):
        return jsonify({"error": "'role' must be a string"}), 400

    role = _sanitize_text(role_value) or "Software Developer"
    if len(role) > MAX_ROLE_LENGTH:
        return jsonify({"error": f"'role' must be <= {MAX_ROLE_LENGTH} characters"}), 400

    try:
        create_interview(room_id, role, candidate_name)
        return jsonify({"status": "created", "room_id": room_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@interview_bp.route("/api/interview/<room_id>", methods=["GET"])
def get(room_id):
    interview = get_interview(room_id)

    if interview:
        return jsonify(dict(interview))

    return jsonify({"error": "Interview not found"}), 404


@interview_bp.route("/api/interview/<room_id>/answers", methods=["POST"])
def save(room_id):
    data, error = _require_json_object()
    if error:
        return error

    answers, answers_error = _validate_required_string(
        data, "answers", MAX_ANSWERS_LENGTH
    )
    if answers_error:
        return jsonify({"error": answers_error}), 400

    if not get_interview(room_id):
        return jsonify({"error": "Interview not found"}), 404

    try:
        save_answers(room_id, answers)
        return jsonify({"status": "answers_saved"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
