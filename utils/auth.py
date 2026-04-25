"""
Room-scoped session authentication.

Flow:
  1. POST /api/interview/create  → server stores room_id in session['owned_rooms']
                                   and returns a signed room_token in the response.
  2. Client stores the token and sends it as the X-Room-Token header (or JSON field
     `room_token`) on every subsequent request.
  3. @require_room_token validates the token and injects `g.room_id` for the view.
"""

import hmac
import hashlib
import time
from functools import wraps
from flask import request, session, jsonify, g, current_app


# ── Token helpers ─────────────────────────────────────────────────────────────

def _sign(room_id: str, secret: str) -> str:
    """Return HMAC-SHA256 hex digest of room_id."""
    return hmac.new(secret.encode(), room_id.encode(), hashlib.sha256).hexdigest()


def generate_room_token(room_id: str) -> str:
    """
    Produce a signed token: "<room_id>.<hmac>".
    The room_id is embedded so the server can verify without a DB lookup.
    """
    secret = current_app.config["SECRET_KEY"]
    sig = _sign(room_id, secret)
    return f"{room_id}.{sig}"


def verify_room_token(token: str) -> str | None:
    """
    Verify the token and return the room_id it is scoped to, or None if invalid.
    Uses hmac.compare_digest to prevent timing attacks.
    """
    if not token or "." not in token:
        return None

    try:
        room_id, provided_sig = token.rsplit(".", 1)
    except ValueError:
        return None

    if not room_id:
        return None

    secret = current_app.config["SECRET_KEY"]
    expected_sig = _sign(room_id, secret)

    if hmac.compare_digest(expected_sig, provided_sig):
        return room_id

    return None


# ── Session helpers ───────────────────────────────────────────────────────────

def grant_room_access(room_id: str) -> None:
    """Record that the current browser session owns this room."""
    owned = session.get("owned_rooms", [])
    if room_id not in owned:
        owned.append(room_id)
    session["owned_rooms"] = owned
    session.modified = True


def session_owns_room(room_id: str) -> bool:
    """Return True if the current session was granted access to room_id."""
    return room_id in session.get("owned_rooms", [])


# ── Decorator ─────────────────────────────────────────────────────────────────

def require_room_token(f):
    """
    Decorator that enforces room-scoped authentication.

    Accepts the token from (in priority order):
      1. X-Room-Token request header
      2. JSON body field `room_token`
      3. Flask session (owned_rooms list) — fallback for same-browser requests

    On success, sets g.room_id to the verified room_id.
    On failure, returns 401.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("X-Room-Token")

        # Fall back to JSON body token
        if not token:
            body = request.get_json(silent=True) or {}
            token = body.get("room_token")

        if token:
            room_id = verify_room_token(token)
            if not room_id:
                return jsonify({"error": "Invalid or expired room token"}), 401
            g.room_id = room_id
            return f(*args, **kwargs)

        # Fall back to session ownership (same-browser, no explicit token)
        # Extract room_id from URL kwargs or JSON body
        url_room_id = kwargs.get("room_id")
        if not url_room_id:
            body = request.get_json(silent=True) or {}
            url_room_id = body.get("room_id")

        if url_room_id and session_owns_room(url_room_id):
            g.room_id = url_room_id
            return f(*args, **kwargs)

        return jsonify({"error": "Authentication required. Provide a valid X-Room-Token header."}), 401

    return decorated


def verify_socket_token(token: str, room_id: str) -> bool:
    """
    Verify a room token for SocketIO events.
    Returns True if the token is valid and scoped to the given room_id.
    """
    verified_room = verify_room_token(token)
    return verified_room == room_id
