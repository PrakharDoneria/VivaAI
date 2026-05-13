#!/usr/bin/env python3
"""
Verify Issue #25 acceptance without calling external AI APIs.
Run from repo root: python scripts/verify_issue_25.py
"""
import subprocess
import uuid
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import app  # noqa: E402
from models.interview import init_db  # noqa: E402


def main() -> int:
    init_db()
    client = app.test_client()
    body = {
        "role": "Software Developer",
        "answer": None,
        "question_history": [],
    }

    app.config["VIVAAI_API_KEY"] = ""
    rid1 = uuid.uuid4().hex[:8].upper()
    with patch("routes.ai_routes.generate_question", return_value="Hello?"):
        with patch("routes.ai_routes.generate_voice", return_value="/static/x.wav"):
            r = client.post("/api/interview/create", json={
                "room_id": rid1,
                "role": "Software Developer",
                "candidate_name": "Test",
                "duration": 10,
            })
            assert r.status_code != 401, "mutating route should not require key when unset"

            r = client.post("/api/ai/question", json=body)
            assert r.status_code != 401, f"expected not 401 when key unset, got {r.status_code}"

    print("OK: no 401 when VIVAAI_API_KEY empty (interview create + AI question)")

    app.config["VIVAAI_API_KEY"] = "test-secret-key-issue25"
    r = client.post("/api/ai/question", json=body)
    assert r.status_code == 401, r.status_code
    r = client.post("/api/ai/question", json=body, headers={"X-API-Key": "nope"})
    assert r.status_code == 401
    print("OK: 401 without / with wrong X-API-Key")

    with patch("routes.ai_routes.generate_question", return_value="Hello?"):
        with patch("routes.ai_routes.generate_voice", return_value="/static/x.wav"):
            r = client.post(
                "/api/ai/question",
                json=body,
                headers={"X-API-Key": "test-secret-key-issue25"},
            )
            assert r.status_code == 200, (r.status_code, r.get_data(as_text=True)[:400])

    rid2 = uuid.uuid4().hex[:8].upper()
    r = client.post(
        "/api/interview/create",
        json={
            "room_id": rid2,
            "role": "Software Developer",
            "candidate_name": "T",
            "duration": 10,
        },
        headers={"X-API-Key": "test-secret-key-issue25"},
    )
    assert r.status_code == 200, r.get_data(as_text=True)
    print("OK: 200 with valid X-API-Key on AI + interview create")

    rc = subprocess.call(
        [sys.executable, str(ROOT / "scripts" / "_issue25_rate_subprocess.py")],
        cwd=str(ROOT),
    )
    assert rc == 0
    print("\nAll Issue #25 verification checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
