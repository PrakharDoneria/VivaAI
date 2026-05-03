from flask import Blueprint, render_template, jsonify
from models.analytics import get_analytics_data

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/analytics")
def analytics_page():
    """Serve the analytics dashboard page."""
    return render_template("analytics.html")


@analytics_bp.route("/api/analytics", methods=["GET"])
def analytics_api():
    """Return analytics data as JSON for the dashboard."""
    try:
        data = get_analytics_data()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
