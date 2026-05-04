from functools import wraps
from flask import request, jsonify
from models.user import UserModel

def login_required(f):
    """Decorator to require authentication for routes"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not token:
            return jsonify({"error": "Authentication required", "message": "Please login first"}), 401
        
        user_id = UserModel.verify_token(token)
        if not user_id:
            return jsonify({"error": "Invalid or expired token", "message": "Please login again"}), 401
        
        current_user = UserModel.get_user_by_id(user_id)
        if not current_user:
            return jsonify({"error": "User not found"}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated