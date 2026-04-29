import threading
from flask_socketio import emit, join_room, leave_room

_rooms: dict[str, set[str]] = {}
_room_lock = threading.Lock()


def _add_to_room(room_id, sid):
    with _room_lock:
        _rooms.setdefault(room_id, set()).add(sid)


def _remove_from_room(room_id, sid):
    with _room_lock:
        if room_id in _rooms:
            _rooms[room_id].discard(sid)
            if not _rooms[room_id]:
                del _rooms[room_id]


def _count_in_room(room_id):
    with _room_lock:
        return len(_rooms.get(room_id, set()))


def register_signaling_events(socketio):
    """Register socket handlers for room join/leave and SDP/ICE exchange."""

    def validate_room(data):
        room = (data or {}).get("room")
        if not room or not isinstance(room, str) or len(room) > 50:
            return None
        return room

    @socketio.on("join-room")
    def on_join(data):
        from flask import request as flask_request

        room = validate_room(data)
        if not room:
            return

        sid = flask_request.sid
        join_room(room)
        _add_to_room(room, sid)

        emit("room-joined", {"room": room, "is_initiator": _count_in_room(room) == 1})
        emit("user-joined", {"room": room}, to=room, include_self=False)

    @socketio.on("offer")
    def on_offer(data):
        room = validate_room(data)
        if room:
            emit("offer", data, to=room, include_self=False)

    @socketio.on("answer")
    def on_answer(data):
        room = validate_room(data)
        if room:
            emit("answer", data, to=room, include_self=False)

    @socketio.on("ice-candidate")
    def on_ice_candidate(data):
        room = validate_room(data)
        if room:
            emit("ice-candidate", data, to=room, include_self=False)

    @socketio.on("leave-room")
    def on_leave(data):
        from flask import request as flask_request

        room = validate_room(data)
        if not room:
            return

        sid = flask_request.sid
        leave_room(room)
        _remove_from_room(room, sid)
        emit("user-left", {"room": room}, to=room)

    @socketio.on("disconnect")
    def on_disconnect():
        from flask import request as flask_request

        sid = flask_request.sid
        with _room_lock:
            rooms_for_sid = [room_id for room_id, members in _rooms.items() if sid in members]

        for room_id in rooms_for_sid:
            _remove_from_room(room_id, sid)
            emit("user-left", {"room": room_id}, to=room_id)
