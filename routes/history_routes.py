import csv
import io
import json
from flask import Blueprint, request, jsonify, render_template, Response
from models.interview import get_all_interviews, get_interview, get_interviews_by_ids

history_bp = Blueprint("history", __name__)


@history_bp.route("/history")
def history_page():
    return render_template("history.html")


@history_bp.route("/api/history", methods=["GET"])
def list_interviews():
    try:
        interviews = get_all_interviews()
        return jsonify({"interviews": interviews})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _interview_to_export_dict(row):
    """Convert a raw interview DB row (dict) into a clean export dict."""
    qa_history = []
    if row.get("qa_history"):
        try:
            qa_history = json.loads(row["qa_history"])
        except (json.JSONDecodeError, TypeError):
            qa_history = []

    return {
        "candidate_name": row.get("candidate_name", ""),
        "role": row.get("role", ""),
        "room_id": row.get("room_id", ""),
        "duration_minutes": row.get("duration", ""),
        "status": row.get("status", ""),
        "created_at": row.get("created_at", ""),
        "ended_at": row.get("ended_at", ""),
        "qa_history": qa_history,
        "report": row.get("report", ""),
    }


def _build_csv(interviews_export):
    """Build a CSV string from a list of export dicts."""
    output = io.StringIO()

    # Determine max number of Q&A pairs across all interviews
    max_qa = 0
    for item in interviews_export:
        qa_len = len(item.get("qa_history", []))
        if qa_len > max_qa:
            max_qa = qa_len

    # Build header
    header = ["candidate_name", "role", "room_id", "duration_minutes", "status", "created_at", "ended_at"]
    for i in range(1, max_qa + 1):
        header.append(f"question_{i}")
        header.append(f"answer_{i}")
    header.append("report")

    writer = csv.writer(output)
    writer.writerow(header)

    for item in interviews_export:
        row = [
            item.get("candidate_name", ""),
            item.get("role", ""),
            item.get("room_id", ""),
            item.get("duration_minutes", ""),
            item.get("status", ""),
            item.get("created_at", ""),
            item.get("ended_at", ""),
        ]
        qa = item.get("qa_history", [])
        for i in range(max_qa):
            if i < len(qa):
                row.append(qa[i].get("question", ""))
                row.append(qa[i].get("answer", ""))
            else:
                row.append("")
                row.append("")
        row.append(item.get("report", ""))
        writer.writerow(row)

    return output.getvalue()


@history_bp.route("/api/export/<room_id>", methods=["GET"])
def export_single(room_id):
    fmt = request.args.get("format", "json").lower()
    interview = get_interview(room_id)

    if not interview:
        return jsonify({"error": "Interview not found"}), 404

    export_data = _interview_to_export_dict(dict(interview))

    if fmt == "csv":
        csv_str = _build_csv([export_data])
        return Response(
            csv_str,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename=interview_{room_id}.csv"}
        )

    return Response(
        json.dumps(export_data, indent=2, default=str),
        mimetype="application/json",
        headers={"Content-Disposition": f"attachment; filename=interview_{room_id}.json"}
    )


@history_bp.route("/api/export/batch", methods=["POST"])
def export_batch():
    fmt = request.args.get("format", "json").lower()
    body = request.get_json(silent=True) or {}
    room_ids = body.get("room_ids", [])

    if not room_ids or not isinstance(room_ids, list):
        return jsonify({"error": "Provide a non-empty list of room_ids"}), 400

    # Sanitize: only allow alphanumeric + hyphen room IDs
    import re
    clean_ids = [rid for rid in room_ids if isinstance(rid, str) and re.match(r"^[A-Z0-9-]{1,50}$", rid, re.I)]

    if not clean_ids:
        return jsonify({"error": "No valid room IDs provided"}), 400

    interviews = get_interviews_by_ids(clean_ids)
    export_list = [_interview_to_export_dict(row) for row in interviews]

    if fmt == "csv":
        csv_str = _build_csv(export_list)
        return Response(
            csv_str,
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=interviews_export.csv"}
        )

    return Response(
        json.dumps(export_list, indent=2, default=str),
        mimetype="application/json",
        headers={"Content-Disposition": "attachment; filename=interviews_export.json"}
    )
