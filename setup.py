"""VivaAI Setup Script.

Run: python setup.py
"""

import sys
import subprocess
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
REQUIREMENTS_FILE = BASE_DIR / "requirements.txt"
ENV_FILE = BASE_DIR / ".env"
ENV_EXAMPLE = BASE_DIR / ".env.example"
REQUIRED_DIRS = [
    BASE_DIR / "database",
    BASE_DIR / "static" / "audio" / "questions",
    BASE_DIR / "static" / "audio" / "answers",
]
REQUIRED_PACKAGES = [
    ("flask", "flask"),
    ("flask_socketio", "flask-socketio"),
    ("dotenv", "python-dotenv"),
    ("eventlet", "eventlet"),
]


def run_cmd(cmd, check=True):
    print("  >", " ".join(cmd))
    completed = subprocess.run(cmd, check=False)
    if check and completed.returncode:
        print(f"  FAILED (exit code {completed.returncode})")
        return False
    return True


def check_python():
    version = sys.version_info
    print(f"  Python {version.major}.{version.minor}.{version.micro}")
    if version < (3, 9):
        raise SystemExit("  ERROR: Python 3.9+ is required.")
    print("  OK - Python version")


def ensure_pip():
    try:
        import pip  # noqa: F401
        print("  OK - pip is available")
    except ImportError:
        print("  Installing pip...")
        run_cmd([sys.executable, "-m", "ensurepip", "--upgrade"])


def install_requirements():
    if not REQUIREMENTS_FILE.exists():
        print("  ERROR: requirements.txt not found")
        return False

    print("  Installing from requirements.txt...")
    if run_cmd([sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE), "--upgrade"]):
        print("  OK - Dependencies installed")
        return True
    return False


def setup_env():
    if ENV_FILE.exists():
        print("  OK - .env file already exists")
        return

    if ENV_EXAMPLE.exists():
        shutil.copy(ENV_EXAMPLE, ENV_FILE)
        print("  OK - .env created from .env.example")
        return

    ENV_FILE.write_text(
        "SECRET_KEY=vivaai-super-secret-key-change-me\n"
        "SARVAM_API_KEY=your_sarvam_api_key_here\n"
        "DEBUG=True\n"
        "PORT=5000\n"
        "HOST=0.0.0.0\n"
        "INTERVIEW_DURATION_MINUTES=10\n"
        "MAX_QUESTIONS=6\n",
        encoding="utf-8",
    )
    print("  OK - .env file created with defaults")
    print("  WARN: Please set your SARVAM_API_KEY in the .env file!")


def setup_directories():
    for path in REQUIRED_DIRS:
        path.mkdir(parents=True, exist_ok=True)
        (path / ".gitkeep").touch(exist_ok=True)
    print("  OK - Created required directories")


def init_database():
    sys.path.insert(0, str(BASE_DIR))
    try:
        from models.interview import init_db

        init_db()
        print("  OK - Database initialized (database/vivaai.db)")
    except Exception as exc:
        print(f"  WARN: Database init skipped: {exc}")


def verify_install():
    all_ok = True
    for module, package in REQUIRED_PACKAGES:
        try:
            __import__(module)
            print(f"  OK - {package}")
        except ImportError:
            print(f"  MISSING - {package}")
            all_ok = False
    return all_ok


def main():
    print("\n" + "=" * 50)
    print("  VivaAI -- Setup Script")
    print("=" * 50)

    print("\n[1/5] Checking Python version...")
    check_python()

    print("\n[2/5] Checking pip...")
    ensure_pip()

    print("\n[3/5] Installing dependencies...")
    install_requirements()

    print("\n[4/5] Setting up project files...")
    setup_env()
    setup_directories()

    print("\n[5/5] Verifying installation...")
    ok = verify_install()

    print("\n[DB] Initializing database...")
    init_database()

    print("\n" + "=" * 50)
    if ok:
        print("  DONE! Setup complete.")
        print("\n  Next steps:")
        print("  1. Edit .env and set your SARVAM_API_KEY")
        print("  2. Run:  python app.py")
        print("  3. Open: http://localhost:5000")
    else:
        print("  Setup completed with warnings - check errors above.")
    print("=" * 50)


if __name__ == "__main__":
    main()
