import os
from dotenv import load_dotenv

load_dotenv()

from flask import Flask, render_template
from flask_socketio import SocketIO

from config import Config, validate_config
from models.interview import init_db
from routes.ai_routes import ai_bp
from routes.interview_routes import interview_bp
from webrtc.signaling import register_signaling_events

validate_config()

app = Flask(__name__)
app.config.from_object(Config)

socketio = SocketIO(
    app,
    cors_allowed_origins=Config.CORS_ALLOWED_ORIGINS,
    async_mode="threading",
    logger=False,
    engineio_logger=False,
)

app.register_blueprint(ai_bp)
app.register_blueprint(interview_bp)
register_signaling_events(socketio)


@app.after_request
def set_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(self), microphone=(self)"
    if Config.ENVIRONMENT == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


@app.route("/")
def home():
    return render_template("index.html")


@app.errorhandler(404)
def not_found(_error):
    return render_template("index.html"), 404


if __name__ == "__main__":
    init_db()
    os.makedirs(Config.AUDIO_FOLDER, exist_ok=True)
    os.makedirs(Config.ANSWERS_FOLDER, exist_ok=True)
    os.makedirs("database", exist_ok=True)

    print("  VivaAI Interview Platform")
    print(f"  Running at http://{Config.HOST}:{Config.PORT}")
    print(f"  Local Access: http://localhost:{Config.PORT}")
    print(f"  Debug: {Config.DEBUG}")

    socketio.run(app, host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
