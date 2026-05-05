"""
VivaAI Setup Script
Installs all dependencies and sets up the project for first run.
Run: python setup.py
"""

import sys
import os
import subprocess
import shutil

# Force UTF-8 output on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def run(cmd, check=True):
    print(f"  > {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False, check=False)
    if check and result.returncode != 0:
        print(f"  FAILED (exit code {result.returncode})")
        return False
    return True


def check_python():
    version = sys.version_info
    print(f"  Python {version.major}.{version.minor}.{version.micro}")
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("  ERROR: Python 3.9+ is required.")
        sys.exit(1)
    print("  OK - Python version")


def ensure_pip():
    try:
        import pip  # noqa: F401
        print("  OK - pip is available")
    except ImportError:
        print("  Installing pip...")
        run([sys.executable, "-m", "ensurepip", "--upgrade"])


def install_requirements():
    req_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
    if not os.path.exists(req_file):
        print("  ERROR: requirements.txt not found")
        return False

    print("  Installing from requirements.txt...")
    ok = run([sys.executable, "-m", "pip", "install", "-r", req_file, "--upgrade"])
    if ok:
        print("  OK - Dependencies installed")
    return ok


def setup_env():
    base = os.path.dirname(os.path.abspath(__file__))
    env_file = os.path.join(base, ".env")
    env_example = os.path.join(base, ".env.example")

    if os.path.exists(env_file):
        print("  OK - .env file already exists")
        return

    if os.path.exists(env_example):
        shutil.copy(env_example, env_file)
        print("  OK - .env created from .env.example")
    else:
        default_env = (
            "SECRET_KEY=vivaai-super-secret-key-change-me\n"
            "SARVAM_API_KEY=your_sarvam_api_key_here\n"
            "DEBUG=True\n"
            "PORT=5000\n"
            "HOST=0.0.0.0\n"
            "INTERVIEW_DURATION_MINUTES=10\n"
            "MAX_QUESTIONS=6\n"
        )
        with open(env_file, "w", encoding="utf-8") as f:
            f.write(default_env)
        print("  OK - .env file created with defaults")
        print("  WARN: Please set your SARVAM_API_KEY in the .env file!")


def setup_directories():
    base = os.path.dirname(os.path.abspath(__file__))
    dirs = [
        "database",
        "static/audio/questions",
        "static/audio/answers",
    ]
    for d in dirs:
        path = os.path.join(base, d)
        os.makedirs(path, exist_ok=True)
        gitkeep = os.path.join(path, ".gitkeep")
        if not os.path.exists(gitkeep):
            open(gitkeep, "w").close()
    print(f"  OK - Created {len(dirs)} required directories")


def init_database():
    base = os.path.dirname(os.path.abspath(__file__))
    if base not in sys.path:
        sys.path.insert(0, base)
    try:
        from models.interview import init_db
        init_db()
        print("  OK - Database initialized (database/vivaai.db)")
    except Exception as e:
        print(f"  WARN: Database init skipped: {e}")


def verify_install():
    packages = [
        ("flask", "flask"),
        ("flask_socketio", "flask-socketio"),
        ("dotenv", "python-dotenv"),
        ("eventlet", "eventlet"),
        ("bcrypt", "bcrypt"),
        ("jwt", "PyJWT"),
    ]
    all_ok = True
    for import_name, pkg_name in packages:
        try:
            __import__(import_name)
            print(f"  OK - {pkg_name}")
        except ImportError:
            print(f"  MISSING - {pkg_name}")
            all_ok = False
    return all_ok


def main():
    print()
    print("=" * 50)
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

    print()
    print("=" * 50)
    if ok:
        print("  DONE! Setup complete.")
        print()
        print("  Next steps:")
        print("  1. Edit .env and set your SARVAM_API_KEY")
        print("  2. Run:  python app.py")
        print("  3. Open: http://localhost:5000")
    else:
        print("  Setup completed with warnings - check errors above.")
    print("=" * 50)
    print()


if __name__ == "__main__":
    main()