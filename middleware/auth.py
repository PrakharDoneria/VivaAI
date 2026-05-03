from functools import wraps
from flask import request, jsonify, current_app
import secrets


def require_api_key(f):
    """Decorator to require API key for protected endpoints"""
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        expected_key = current_app.config.get('API_SECRET_KEY')
        
        if not api_key or not expected_key or not secrets.compare_digest(api_key, expected_key):
            return jsonify({
                "error": "Unauthorized",
                "message": "Valid X-API-Key header required"
            }), 401
        return f(*args, **kwargs)
    return decorated