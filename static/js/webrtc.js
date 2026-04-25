// webrtc.js — WebRTC peer connection management

let localStream = null;
let peerConnection = null;
let currentRoomId = null;
let isInitiator = false;

const RTC_CONFIG = {
    iceServers: [
        { urls: "stun:stun.l.google.com:19302" },
        { urls: "stun:stun1.l.google.com:19302" },
        { urls: "stun:stun2.l.google.com:19302" },
    ]
};

// ── Media ────────────────────────────────────────────────

async function startMedia() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        showStatus("Your browser does not support camera/microphone access. Please use a modern browser.", "error");
        return false;
    }

    try {
        localStream = await navigator.mediaDevices.getUserMedia({
            video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: "user" },
            audio: { echoCancellation: true, noiseSuppression: true, sampleRate: 44100 }
        });
        document.getElementById("localVideo").srcObject = localStream;
        console.log("[WebRTC] Media started");

        // Clear error if now successful
        const el = document.getElementById("statusMsg");
        if (el && el.classList.contains("status-error")) {
            el.style.display = "none";
        }

        return true;
    } catch (err) {
        console.error("[WebRTC] getUserMedia error:", err);

        let message = "Camera/mic access denied. Please allow permissions in your browser.";
        let showRetry = true;

        if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
            message = "<strong>Permissions denied.</strong> Please click the camera icon in your address bar to allow access and try again.";
        } else if (err.name === "NotFoundError" || err.name === "DevicesNotFoundError") {
            message = "<strong>No devices found.</strong> Please connect a camera/microphone.";
        } else if (err.name === "NotReadableError" || err.name === "TrackStartError") {
            message = "<strong>Hardware error.</strong> Your camera/mic might be in use by another app.";
        }

        const html = `
            <div style="display: flex; align-items: center; justify-content: space-between; gap: 12px; width: 100%;">
                <span>${message}</span>
                ${showRetry ? `<button class="btn btn-ghost btn-sm" onclick="retryPermission()" style="border-color: currentColor; color: inherit; background: rgba(255,255,255,0.1);">Retry</button>` : ""}
            </div>
        `;

        showStatusHTML(html, "error");
        return false;
    }
}

// Global retry helper
window.retryPermission = async function () {
    showStatus("Retrying media access…", "info");
    const ok = await startMedia();
    if (ok) {
        showStatus("Permissions granted! Joining room…", "success");
        if (typeof roomId !== "undefined") joinRoom(roomId);
    }
};

function stopMedia() {
    if (localStream) {
        localStream.getTracks().forEach(t => t.stop());
        localStream = null;
    }
}

function toggleMute() {
    if (!localStream) return;
    const audioTrack = localStream.getAudioTracks()[0];
    if (audioTrack) {
        audioTrack.enabled = !audioTrack.enabled;
        const btn = document.getElementById("muteBtn");
        if (btn) btn.textContent = audioTrack.enabled ? "🎤 Mute" : "🔇 Unmute";
    }
}

function toggleVideo() {
    if (!localStream) return;
    const videoTrack = localStream.getVideoTracks()[0];
    if (videoTrack) {
        videoTrack.enabled = !videoTrack.enabled;
        const btn = document.getElementById("videoBtn");
        if (btn) btn.textContent = videoTrack.enabled ? "📹 Stop Video" : "📹 Start Video";
    }
}

// ── Peer Connection ───────────────────────────────────────

function createPeerConnection(roomId) {
    if (peerConnection) {
        peerConnection.close();
    }

    currentRoomId = roomId;
    peerConnection = new RTCPeerConnection(RTC_CONFIG);

    // Add local tracks
    if (localStream) {
        localStream.getTracks().forEach(track => {
            peerConnection.addTrack(track, localStream);
        });
    }

    // Remote stream
    peerConnection.ontrack = event => {
        const remoteVideo = document.getElementById("remoteVideo");
        if (remoteVideo) remoteVideo.srcObject = event.streams[0];
        showStatus("Video connection established!", "success");
    };

    // ICE candidates
    peerConnection.onicecandidate = event => {
        if (event.candidate) {
            socket.emit("ice-candidate", {
                room: roomId,
                candidate: event.candidate,
                token: _roomToken()
            });
        }
    };

    peerConnection.oniceconnectionstatechange = () => {
        console.log("[WebRTC] ICE state:", peerConnection.iceConnectionState);
        if (peerConnection.iceConnectionState === "disconnected" ||
            peerConnection.iceConnectionState === "failed") {
            showStatus("Video connection lost. Reconnecting…", "warning");
        }
    };

    peerConnection.onconnectionstatechange = () => {
        console.log("[WebRTC] Connection state:", peerConnection.connectionState);
    };

    return peerConnection;
}

async function createOffer(roomId) {
    createPeerConnection(roomId);

    const offer = await peerConnection.createOffer();
    await peerConnection.setLocalDescription(offer);

    socket.emit("offer", { room: roomId, offer: offer, token: _roomToken() });
    console.log("[WebRTC] Offer sent");
}

window.handleOffer = async function (data) {
    console.log("[WebRTC] Received offer");
    createPeerConnection(data.room);

    await peerConnection.setRemoteDescription(new RTCSessionDescription(data.offer));
    const answer = await peerConnection.createAnswer();
    await peerConnection.setLocalDescription(answer);

    socket.emit("answer", { room: data.room, answer: answer, token: _roomToken() });
    console.log("[WebRTC] Answer sent");
};

window.handleAnswer = async function (data) {
    console.log("[WebRTC] Received answer");
    if (peerConnection) {
        await peerConnection.setRemoteDescription(new RTCSessionDescription(data.answer));
    }
};

window.handleCandidate = async function (data) {
    if (peerConnection && data.candidate) {
        try {
            await peerConnection.addIceCandidate(new RTCIceCandidate(data.candidate));
        } catch (e) {
            console.warn("[WebRTC] ICE candidate error:", e);
        }
    }
};

// ── Socket callbacks ──────────────────────────────────────

window.onRoomJoined = function (data) {
    isInitiator = data.is_initiator;
    currentRoomId = data.room;
    // If first person, just wait. Offer created when second joins.
};

window.onUserJoined = async function (data) {
    // Second person joined → first person (initiator) creates the offer
    if (isInitiator && localStream) {
        console.log("[WebRTC] User joined, creating offer as initiator");
        await createOffer(data.room);
    }
};

window.onUserLeft = function (data) {
    const remoteVideo = document.getElementById("remoteVideo");
    if (remoteVideo) remoteVideo.srcObject = null;
    if (peerConnection) {
        peerConnection.close();
        peerConnection = null;
    }
};