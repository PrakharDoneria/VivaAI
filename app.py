from pathlib import Path

from flask import Flask, render_template
from flask_socketio import SocketIO

from config import Config
from limiter_ext import limiter
from models.interview import init_db
from routes.ai_routes import ai_bp
from routes.history_routes import history_bp
from routes.interview_routes import interview_bp
from webrtc.signaling import register_signaling_events


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    limiter.init_app(app)

    socketio = SocketIO(
        app,
        cors_allowed_origins="*",
        async_mode="threading",
        logger=False,
        engineio_logger=False,
    )

    for blueprint in (ai_bp, interview_bp, history_bp):
        app.register_blueprint(blueprint)

    register_signaling_events(socketio)

    @app.context_processor
    def inject_client_config():
        return {"vivaai_api_key": app.config.get("VIVAAI_API_KEY") or ""}

    @app.route("/")
    def home():
        return render_template("index.html")

    @app.errorhandler(404)
    def not_found(e):
        return render_template("index.html"), 404

    return app, socketio


def ensure_directories(*paths: str):
    for path in paths:
        Path(path).mkdir(parents=True, exist_ok=True)


def print_startup_info(config: Config):
    print("  VivaAI Interview Platform")
    print(f"  Running at http://{config.HOST}:{config.PORT}")
    print(f"  Local Access: http://localhost:{config.PORT}")
    print(f"  Debug: {config.DEBUG}")


app, socketio = create_app()


if __name__ == "__main__":
    init_db()
    ensure_directories(Config.AUDIO_FOLDER, Config.ANSWERS_FOLDER, "database")
    print_startup_info(Config)

    socketio.run(
        app,
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG,
        allow_unsafe_werkzeug=True,
    )
