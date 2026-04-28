from flask_socketio import emit, join_room, leave_room
from flask import request
from models.interview import get_interview
from threading import Lock

# Track room membership
_rooms = {}
_rooms_lock = Lock()


def _add_to_room(room_id, sid):
    _rooms.setdefault(room_id, set()).add(sid)


def _remove_from_room(room_id, sid):
    if room_id in _rooms:
        _rooms[room_id].discard(sid)
        if not _rooms[room_id]:
            del _rooms[room_id]


def register_signaling_events(socketio):

    def validate_room(data):
        room = data.get("room")
        if not room or not isinstance(room, str) or len(room) > 50:
            return None
        return room

    @socketio.on("join-room")
    def on_join(data):
        room = validate_room(data)
        if not room:
            return

        # ✅ DB validation
        interview = get_interview(room)
        if not interview or interview.get("status") == "ended":
            emit("error", {"message": "Invalid or expired room"})
            return

        # ✅ Capacity check
        with _rooms_lock:
            if len(_rooms.get(room, set())) >= 2:
                emit("error", {"message": "Room is full"})
                return

            _add_to_room(room, request.sid)

        join_room(room)

    @socketio.on("offer")
    def on_offer(data):
        room = validate_room(data)
        if not room:
            return
        emit("offer", data, to=room, include_self=False)

    @socketio.on("answer")
    def on_answer(data):
        room = validate_room(data)
        if not room:
            return
        emit("answer", data, to=room, include_self=False)

    @socketio.on("ice-candidate")
    def on_ice_candidate(data):
        room = validate_room(data)
        if not room:
            return
        emit("ice-candidate", data, to=room, include_self=False)

    @socketio.on("leave-room")
    def on_leave(data):
        room = validate_room(data)
        if not room:
            return

        sid = request.sid
        leave_room(room)
        _remove_from_room(room, sid)

        emit("user-left", {"room": room}, to=room)

    @socketio.on("disconnect")
    def on_disconnect():
        sid = request.sid
        for room_id in list(_rooms.keys()):
            if sid in _rooms.get(room_id, set()):
                _remove_from_room(room_id, sid)