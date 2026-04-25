// socket.js — VivaAI WebSocket client

const socket = io({
    transports: ["websocket", "polling"],
    reconnection: true,
    reconnectionAttempts: 5,
    reconnectionDelay: 1000,
});

let _roomId = null;

function _roomToken() {
    if (!_roomId) return null;
    return sessionStorage.getItem(`room_token_${_roomId}`) || null;
}

function joinRoom(roomId) {
    _roomId = roomId;
    socket.emit("join-room", { room: roomId, token: _roomToken() });
}

function leaveRoom() {
    if (_roomId) {
        socket.emit("leave-room", { room: _roomId, token: _roomToken() });
        _roomId = null;
    }
}

// ── incoming events ──────────────────────────────────────

socket.on("connect", () => {
    console.log("[Socket] Connected:", socket.id);
    // Re-join room on reconnect
    if (_roomId) socket.emit("join-room", { room: _roomId, token: _roomToken() });
});

socket.on("disconnect", () => {
    console.log("[Socket] Disconnected");
    showStatus("Connection lost. Reconnecting…", "warning");
});

socket.on("room-joined", (data) => {
    console.log("[Socket] Room joined, is_initiator:", data.is_initiator);
    if (data.is_initiator) {
        // First person in the room – wait for someone else
        showStatus("Waiting for the interviewer to join…", "info");
    } else {
        // Second person joined – first person should create offer
        showStatus("Connected! Starting peer connection…", "success");
    }
    if (window.onRoomJoined) window.onRoomJoined(data);
});

socket.on("user-joined", (data) => {
    console.log("[Socket] Another user joined:", data.room);
    showStatus("Interviewer connected!", "success");
    if (window.onUserJoined) window.onUserJoined(data);
});

socket.on("user-left", (data) => {
    console.log("[Socket] User left:", data.room);
    showStatus("Other participant disconnected.", "warning");
    if (window.onUserLeft) window.onUserLeft(data);
});

socket.on("offer", (data) => {
    if (window.handleOffer) window.handleOffer(data);
});

socket.on("answer", (data) => {
    if (window.handleAnswer) window.handleAnswer(data);
});

socket.on("ice-candidate", (data) => {
    if (window.handleCandidate) window.handleCandidate(data);
});

socket.on("connect_error", (err) => {
    console.error("[Socket] Connection error:", err.message);
    showStatus("Connection error. Retrying…", "error");
});

socket.on("auth-error", (data) => {
    console.error("[Socket] Auth error:", data.error);
    showStatus("Session expired. Please refresh the page.", "error");
});

function showStatus(msg, type = "info") {
    const el = document.getElementById("statusMsg");
    if (!el) return;
    el.textContent = msg;
    el.className = `status-msg status-${type}`;
    el.style.display = "block";
    if (type === "success") {
        setTimeout(() => { if (el.textContent === msg) el.style.display = "none"; }, 3000);
    }
}

function showStatusHTML(html, type = "info") {
    const el = document.getElementById("statusMsg");
    if (!el) return;
    el.innerHTML = html;
    el.className = `status-msg status-${type}`;
    el.style.display = "block";
}