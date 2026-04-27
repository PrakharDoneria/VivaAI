// audio.js — Browser-side audio recording & speech-to-text (Web Speech API)

let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;
let recognition = null;
let transcriptText = "";
let interimTranscriptText = "";
let speechRecognitionSupported = false;
let currentRecordingMimeType = "audio/webm";

function getRecorderMimeType() {
    if (typeof MediaRecorder === "undefined" || typeof MediaRecorder.isTypeSupported !== "function") {
        return "";
    }

    const preferred = [
        "audio/webm;codecs=opus",
        "audio/webm",
        "audio/mp4",
        "audio/ogg;codecs=opus",
        "audio/ogg"
    ];

    return preferred.find(type => MediaRecorder.isTypeSupported(type)) || "";
}

function extensionFromMimeType(mimeType) {
    const base = (mimeType || "").split(";", 1)[0].toLowerCase();
    const map = {
        "audio/webm": "webm",
        "video/webm": "webm",
        "audio/mp4": "mp4",
        "audio/ogg": "ogg",
        "audio/wav": "wav",
        "audio/x-wav": "wav",
        "audio/mpeg": "mp3",
        "audio/mp3": "mp3"
    };
    return map[base] || "webm";
}

async function transcribeRecordedAudio(audioBlob) {
    try {
        const formData = new FormData();
        const ext = extensionFromMimeType(audioBlob.type);
        formData.append("audio", audioBlob, `answer.${ext}`);

        // Attach room token as a header if available
        const headers = {};
        if (typeof getRoomToken === "function") {
            const token = getRoomToken();
            if (token) headers["X-Room-Token"] = token;
        }

        const response = await fetch("/api/ai/transcribe", {
            method: "POST",
            headers,
            body: formData
        });

        if (!response.ok) {
            const err = await response.json().catch(() => ({}));
            throw new Error(err.error || "Transcription API error");
        }

        const data = await response.json();
        return (data.transcript || "").trim();
    } catch (err) {
        console.warn("[Audio] Backend transcription failed:", err);
        showStatus("Auto transcription failed. You can type your answer to continue.", "warning");
        return "";
    }
}

// ── Speech Recognition (Web Speech API) ──────────────────

function initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        console.warn("[Audio] Speech Recognition not supported in this browser.");
        speechRecognitionSupported = false;
        return null;
    }

    recognition = new SpeechRecognition();
    speechRecognitionSupported = true;
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-IN";

    recognition.onresult = (event) => {
        let interim = "";
        let final = "";

        for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
                final += transcript + " ";
            } else {
                interim += transcript;
            }
        }

        if (final) transcriptText += final;
        interimTranscriptText = interim;

        const liveEl = document.getElementById("liveTranscript");
        if (liveEl) {
            liveEl.textContent = (transcriptText + interim).trim();
        }
    };

    recognition.onerror = (event) => {
        console.error("[Audio] Speech recognition error:", event.error);
        if (event.error === "no-speech") {
            // Restart recognition silently
            if (isRecording && recognition) {
                try { recognition.start(); } catch (e) { }
            }
        }
    };

    recognition.onend = () => {
        // Auto-restart if still recording
        if (isRecording) {
            try { recognition.start(); } catch (e) { }
        }
    };

    return recognition;
}

// ── Recording control ─────────────────────────────────────

async function startRecording() {
    if (isRecording) return;

    try {
        let stream;
        // Try to reuse existing localStream from webrtc.js if available
        if (
            typeof localStream !== "undefined" &&
            localStream &&
            localStream.getAudioTracks().length > 0 &&
            localStream.getAudioTracks()[0].enabled
        ) {
            // Create a new stream with only the audio tracks to avoid MediaRecorder conflicts
            stream = new MediaStream(localStream.getAudioTracks());
            stream.isReused = true;
        } else {
            // If interview audio track is muted/disabled, request a fresh mic stream for answers.
            stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        }

        audioChunks = [];
        transcriptText = "";
        interimTranscriptText = "";

        const recorderMimeType = getRecorderMimeType();
        mediaRecorder = recorderMimeType
            ? new MediaRecorder(stream, { mimeType: recorderMimeType })
            : new MediaRecorder(stream);
        currentRecordingMimeType = mediaRecorder.mimeType || recorderMimeType || "audio/webm";

        mediaRecorder.ondataavailable = event => {
            if (event.data.size > 0) audioChunks.push(event.data);
        };

        mediaRecorder.start(250); // collect chunks every 250ms
        isRecording = true;

        // Start speech recognition
        if (!recognition) initSpeechRecognition();
        if (recognition) {
            try { recognition.start(); } catch (e) { }
        } else {
            showStatus("Speech-to-text is not supported in this browser. You can still record, then type your answer if needed.", "warning");
        }

        // Update UI
        const recBtn = document.getElementById("recordBtn");
        const stopBtn = document.getElementById("stopBtn");
        if (recBtn) { recBtn.disabled = true; recBtn.classList.add("recording"); }
        if (stopBtn) { stopBtn.disabled = false; }

        const liveEl = document.getElementById("liveTranscript");
        if (liveEl) { liveEl.textContent = ""; liveEl.style.display = "block"; }

        console.log("[Audio] Recording started");
    } catch (err) {
        console.error("[Audio] Start recording failed:", err);

        const html = `
            <div style="display: flex; align-items: center; justify-content: space-between; gap: 12px; width: 100%;">
                <span><strong>Microphone access denied.</strong> Click the lock/camera icon in your address bar to allow.</span>
                <button class="btn btn-ghost btn-sm" onclick="retryPermission()" style="border-color: currentColor; color: inherit; background: rgba(255,255,255,0.1);">Retry</button>
            </div>
        `;
        showStatusHTML(html, "error");
    }
}

async function stopRecording() {
    if (!isRecording) return;

    isRecording = false;

    if (recognition) {
        try { recognition.stop(); } catch (e) { }
    }

    return new Promise((resolve) => {
        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: currentRecordingMimeType });
            const liveText = (document.getElementById("liveTranscript")?.textContent || "").trim();
            let answer = (transcriptText + " " + interimTranscriptText).trim() || liveText;

            // If browser recognition misses speech, use backend STT on recorded audio.
            if (!answer) {
                answer = await transcribeRecordedAudio(audioBlob);
            }

            if (!answer) {
                const fallback = window.prompt(
                    speechRecognitionSupported
                        ? "We could not clearly capture your speech. Type your answer and submit:"
                        : "Your browser could not transcribe speech. Type your answer to continue:"
                );
                answer = (fallback || "").trim();
            }

            if (!answer) {
                answer = "I need a moment to gather my thoughts.";
            }

            console.log("[Audio] Recorded answer:", answer);

            // Update UI
            const recBtn = document.getElementById("recordBtn");
            const stopBtn = document.getElementById("stopBtn");
            if (recBtn) { recBtn.disabled = false; recBtn.classList.remove("recording"); }
            if (stopBtn) { stopBtn.disabled = true; }

            // Send answer to AI interviewer
            await sendAnswer(answer);
            resolve(answer);
        };

        if (mediaRecorder && mediaRecorder.state !== "inactive") {
            mediaRecorder.stop();
            // Stop all tracks only if stream was not reused from global localStream
            if (!mediaRecorder.stream.isReused) {
                mediaRecorder.stream.getTracks().forEach(t => t.stop());
            }
        }
    });
}