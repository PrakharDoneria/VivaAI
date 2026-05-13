import secrets
from functools import wraps

from flask import current_app, jsonify, request


def require_api_key(f):
    """
    Require a valid X-API-Key header when VIVAAI_API_KEY is set in config.
    If unset, enforcement is skipped so local dev works without a key.
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        expected = (current_app.config.get("VIVAAI_API_KEY") or "").strip()
        if not expected:
            return f(*args, **kwargs)

        provided = request.headers.get("X-API-Key", "")
        if not secrets.compare_digest(
            provided.encode("utf-8"),
            expected.encode("utf-8"),
        ):
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)

    return decorated
