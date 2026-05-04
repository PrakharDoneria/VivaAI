from flask import Blueprint, request, jsonify, render_template
from models.user import UserModel

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login")
def login_page():
    return render_template("login.html")

@auth_bp.route("/signup")
def signup_page():
    return render_template("signup.html")

@auth_bp.route("/api/auth/signup", methods=["POST"])
def signup():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    
    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400
    
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    
    user = UserModel.create_user(email, password, name)
    if not user:
        return jsonify({"error": "User already exists"}), 409
    
    token = UserModel.generate_token(user['id'])
    return jsonify({"success": True, "user": user, "token": token}), 201

@auth_bp.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400
    
    user = UserModel.authenticate(email, password)
    if not user:
        return jsonify({"error": "Invalid credentials"}), 401
    
    token = UserModel.generate_token(user['id'])
    return jsonify({"success": True, "user": user, "token": token})

@auth_bp.route("/api/auth/me", methods=["GET"])
def get_user():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = UserModel.verify_token(token)
    if not user_id:
        return jsonify({"error": "Invalid token"}), 401
    
    user = UserModel.get_user_by_id(user_id)
    return jsonify({"user": user})