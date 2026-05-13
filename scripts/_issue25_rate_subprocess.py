"""Subprocess helper: fresh Limiter state for 10/min test."""
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import app  # noqa: E402
from models.interview import init_db  # noqa: E402


def main() -> None:
    init_db()
    app.config["VIVAAI_API_KEY"] = "k"
    body = {"role": "Software Developer", "answer": None, "question_history": []}
    c = app.test_client()
    with patch("routes.ai_routes.generate_question", return_value="Q"):
        with patch("routes.ai_routes.generate_voice", return_value="/x"):
            for i in range(10):
                r = c.post("/api/ai/question", json=body, headers={"X-API-Key": "k"})
                assert r.status_code == 200, (i, r.status_code, r.get_data(as_text=True)[:200])
            r = c.post("/api/ai/question", json=body, headers={"X-API-Key": "k"})
            assert r.status_code == 429, "11th request should be rate limited"


if __name__ == "__main__":
    main()
    print("OK: 429 on 11th AI request in 1 minute")
