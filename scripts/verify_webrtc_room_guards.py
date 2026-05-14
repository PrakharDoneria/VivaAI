#!/usr/bin/env python3
"""
Verify WebRTC signaling room guardrails.
Run from repo root: python scripts/verify_webrtc_room_guards.py
"""
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import app, socketio  # noqa: E402
from models.interview import create_interview, end_interview, init_db  # noqa: E402


def assert_event(client, event_name, expected_message=None):
    events = client.get_received()
    for event in events:
        if event["name"] != event_name:
            continue
        if expected_message is not None:
            payload = event["args"][0] if event["args"] else {}
            assert payload.get("message") == expected_message, payload
        return
    raise AssertionError(f"Expected event {event_name!r}, got {events!r}")


def main() -> int:
    init_db()
    flask_client = app.test_client()

    active_room = uuid.uuid4().hex[:8].upper()
    create_interview(active_room, "Engineer", "Candidate", 10)

    client1 = socketio.test_client(app, flask_test_client=flask_client)
    client2 = socketio.test_client(app, flask_test_client=flask_client)
    client3 = socketio.test_client(app, flask_test_client=flask_client)

    client1.emit("join-room", {"room": active_room})
    assert_event(client1, "room-joined")

    client2.emit("join-room", {"room": active_room})
    assert_event(client2, "room-joined")

    client3.emit("join-room", {"room": active_room})
    assert_event(client3, "error", "Room is full")
    print("OK: third participant is rejected from active room")

    ended_room = uuid.uuid4().hex[:8].upper()
    create_interview(ended_room, "Engineer", "Candidate", 10)
    end_interview(ended_room)

    ended_client = socketio.test_client(app, flask_test_client=flask_client)
    ended_client.emit("join-room", {"room": ended_room})
    assert_event(ended_client, "error", "Invalid or expired room")
    print("OK: ended interview room is rejected")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
