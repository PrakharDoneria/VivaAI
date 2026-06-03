// interview.js — AI interview logic

let questionHistory = [];
let currentQuestion = "";
let questionCount = 0;
let interviewActive = false;
let interviewTimer = null;
let qTimer = null;
let timeRemaining = 0;
let qTimeRemaining = 0;
let roleValue = "Software Developer";
let interviewDurationMins = 10;

const MAX_QUESTIONS = 6;
const Q_DURATION = 120; // 2 minutes per question

function sanitizeAiText(text) {
    if (!text) return "";

    let cleaned = String(text);
    cleaned = cleaned.replace(/<think\b[^>]*>[\s\S]*?<\/think>/gi, "");
    cleaned = cleaned.replace(/<analysis\b[^>]*>[\s\S]*?<\/analysis>/gi, "");
    cleaned = cleaned.replace(/<reasoning\b[^>]*>[\s\S]*?<\/reasoning>/gi, "");
    cleaned = cleaned.replace(/<\/?(think|analysis|reasoning)\b[^>]*>/gi, "");
    cleaned = cleaned.replace(/\n{3,}/g, "\n\n");

    return cleaned.trim();
}

let isSessionPaused = false;
let faceMesh = null;
let faceMeshActive = false;

function pauseSession(reason) {
    if (isSessionPaused || !interviewActive) return;
    isSessionPaused = true;
    console.log("[Interview] Session paused:", reason);

    // Show pause overlay
    const overlay = document.getElementById("pauseOverlay");
    const reasonEl = document.getElementById("pauseReason");
    if (overlay) overlay.style.display = "flex";
    if (reasonEl) reasonEl.textContent = reason;

    // Pause timers
    if (interviewTimer) clearInterval(interviewTimer);
    if (qTimer) clearInterval(qTimer);

    // Pause recording if active
    if (typeof isRecording !== "undefined" && isRecording) {
        if (typeof mediaRecorder !== "undefined" && mediaRecorder && mediaRecorder.state === "recording") {
            mediaRecorder.pause();
        }
        if (typeof recognition !== "undefined" && recognition) {
            try { recognition.stop(); } catch (e) { }
        }
    }
    
    // Pause AI voice audio if playing
    const aiVoice = document.getElementById("aiVoice");
    if (aiVoice && !aiVoice.paused) {
        aiVoice.pause();
    }
}

function resumeSession() {
    if (!isSessionPaused || !interviewActive) return;
    isSessionPaused = false;
    console.log("[Interview] Session resumed");

    // Hide pause overlay
    const overlay = document.getElementById("pauseOverlay");
    if (overlay) overlay.style.display = "none";

    // Resume timers
    interviewTimer = setInterval(() => {
        timeRemaining--;
        updateTimerDisplay();
        if (timeRemaining <= 0) {
            clearInterval(interviewTimer);
            endInterview();
        }
    }, 1000);

    // Only resume qTimer if it was actually running (i.e. AI is waiting for answer)
    const indicator = document.getElementById("aiIndicator");
    if (indicator && indicator.className.includes("ai-waiting")) {
        const ring = document.getElementById("qTimerRing");
        if (ring) ring.style.display = "flex";
        qTimer = setInterval(() => {
            qTimeRemaining--;
            updateQuestionTimerUI();
            if (qTimeRemaining <= 0) {
                stopQuestionTimer();
                handleQuestionTimeout();
            }
        }, 1000);
    }

    // Resume recording if active
    if (typeof isRecording !== "undefined" && isRecording) {
        if (typeof mediaRecorder !== "undefined" && mediaRecorder && mediaRecorder.state === "paused") {
            mediaRecorder.resume();
        }
        if (typeof recognition !== "undefined" && recognition) {
            try { recognition.start(); } catch (e) { }
        }
    }

    // Resume AI voice audio if it was paused
    const aiVoice = document.getElementById("aiVoice");
    if (aiVoice && aiVoice.paused && aiVoice.src && !aiVoice.ended) {
        aiVoice.play().catch(e => console.warn("[Interview] Audio resume failed:", e));
    }

    showStatus("Session resumed!", "success");
}

// ── Init ─────────────────────────────────────────────────

function initInterview() {
    // Read room meta from page
    const metaRole = document.getElementById("metaRole");
    if (metaRole) roleValue = metaRole.value || roleValue;

    const metaDuration = document.getElementById("metaDuration");
    if (metaDuration) interviewDurationMins = parseInt(metaDuration.value) || 10;

    // Set up button states
    const stopBtn = document.getElementById("stopBtn");
    if (stopBtn) stopBtn.disabled = true;

    updateProgress();
    updateTimerDisplay(interviewDurationMins * 60);
}

// ── Start interview ───────────────────────────────────────

async function startInterview() {
    if (interviewActive) return;

    // Check if media is ready before proceeding
    if (typeof localStream === "undefined" || !localStream) {
        showStatus("Please allow camera/microphone access to begin the interview.", "warning");
        const ok = await startMedia();
        if (!ok) return;
    }

    const startBtn = document.getElementById("startBtn");
    if (startBtn) startBtn.disabled = true;

    // Preparation Countdown
    for (let i = 3; i > 0; i--) {
        showStatus(`Interview starting in ${i}...`, "warning");
        if (startBtn) startBtn.textContent = `Starting in ${i}...`;
        await new Promise(r => setTimeout(r, 1000));
    }

    interviewActive = true;
    if (startBtn) startBtn.textContent = "Interview in progress…";

    // Initialize proctoring using session.js startProctoring helper
    const videoElement = document.getElementById("localVideo");
    if (typeof startProctoring === "function" && videoElement) {
        try {
            await startProctoring(videoElement);
        } catch (err) {
            console.error("[Interview] Proctoring start failed:", err);
        }
    }

    showStatus("AI Interviewer is preparing your first question…", "info");
    setQuestionStatus("thinking");

    startCountdownTimer();
    await fetchNextQuestion(null);
}

// ── Fetch question from AI ────────────────────────────────

async function fetchNextQuestion(answerText) {
    if (questionCount >= MAX_QUESTIONS) {
        await endInterview();
        return;
    }

    setQuestionStatus("thinking");

    try {
        const response = await fetch("/api/ai/question", {
            method: "POST",
            headers: vivaaiApiHeaders({ "Content-Type": "application/json" }),
            body: JSON.stringify({
                role: roleValue,
                answer: answerText,
                question_history: questionHistory
            })
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || "API error");
        }

        const data = await response.json();
        currentQuestion = sanitizeAiText(data.question);
        questionCount++;

        // Store in history (answer will be added when user responds)
        questionHistory.push({ question: currentQuestion, answer: "" });

        // Display question
        document.getElementById("question").textContent = currentQuestion;
        updateProgress();
        setQuestionStatus("speaking");

        // Play AI voice
        if (data.audio) {
            const aiVoice = document.getElementById("aiVoice");
            aiVoice.src = data.audio;
            aiVoice.onended = () => {
                setQuestionStatus("waiting");
                // Start Question Timer
                startQuestionTimer();
                
                // Auto-enable record button when AI finishes speaking
                const recBtn = document.getElementById("recordBtn");
                if (recBtn) recBtn.disabled = false;
                showStatus("Your turn! Listening...", "info");

                // Auto open mic
                if (typeof startRecording === "function") {
                    startRecording();
                }
            };
            aiVoice.play().catch(e => {
                console.warn("[Interview] Audio play failed:", e);
                setQuestionStatus("waiting");
                startQuestionTimer();
            });
        } else {
            setQuestionStatus("waiting");
            startQuestionTimer();
        }

    } catch (err) {
        console.error("[Interview] Fetch question error:", err);
        showStatus("Error fetching question: " + err.message, "error");
        setQuestionStatus("error");
    }
}

// ── Send answer ───────────────────────────────────────────

async function sendAnswer(answerText) {
    if (!interviewActive) return;

    // Stop Question Timer
    stopQuestionTimer();

    // Store answer in history
    if (questionHistory.length > 0) {
        questionHistory[questionHistory.length - 1].answer = answerText;
    }

    // Update transcript display
    const transcriptEl = document.getElementById("liveTranscript");
    if (transcriptEl) transcriptEl.style.display = "none";

    const answerDisplay = document.getElementById("answerDisplay");
    if (answerDisplay) {
        answerDisplay.textContent = `Your answer: "${answerText}"`;
        answerDisplay.style.display = "block";
    }

    showStatus("Processing your answer…", "info");

    // Disable record button during AI response
    const recBtn = document.getElementById("recordBtn");
    if (recBtn) recBtn.disabled = true;

    await fetchNextQuestion(answerText);
}

// ── End interview ─────────────────────────────────────────

async function endInterview() {
    interviewActive = false;
    faceMeshActive = false;
    clearInterval(interviewTimer);
    stopQuestionTimer();

    if (typeof AUDIO_DETECTOR !== "undefined") {
        try {
            AUDIO_DETECTOR.destroy();
        } catch (e) {
            console.warn("[Interview] AUDIO_DETECTOR destroy error:", e);
        }
    }

    showStatus("Interview complete! Generating your report…", "info");
    setQuestionStatus("done");

    const startBtn = document.getElementById("startBtn");
    const recBtn = document.getElementById("recordBtn");
    const stopBtn = document.getElementById("stopBtn");
    if (startBtn) startBtn.style.display = "none";
    if (recBtn) recBtn.disabled = true;
    if (stopBtn) stopBtn.disabled = true;

    try {
        const response = await fetch("/api/ai/report", {
            method: "POST",
            headers: vivaaiApiHeaders({ "Content-Type": "application/json" }),
            body: JSON.stringify({
                role: roleValue,
                qa_history: questionHistory,
                room_id: typeof roomId !== "undefined" ? roomId : null
            })
        });

        const data = await response.json();

        if (data.report) {
            displayReport(sanitizeAiText(data.report));
        }
    } catch (err) {
        console.error("[Interview] Report error:", err);
        showStatus("Error generating report.", "error");
    }
}

// ── Report display ────────────────────────────────────────

function displayReport(reportText) {
    const reportEl = document.getElementById("reportSection");
    const reportContent = document.getElementById("reportContent");

    if (reportEl) reportEl.style.display = "block";
    if (reportContent) {
        // Clear previous content
        reportContent.innerHTML = "";
        // Format report with line breaks safely
        reportText.split("\n").forEach(line => {
            if (line.trim()) {
                const p = document.createElement("p");
                p.textContent = line.trim();
                reportContent.appendChild(p);
            }
        });

        // Append Eye-Tracking Metrics
        const trackerReport = EYE_TRACKER.getReport();
        const statsDiv = document.createElement("div");
        statsDiv.className = "card";
        statsDiv.style.marginTop = "24px";
        statsDiv.style.borderTop = "4px solid var(--accent)";
        statsDiv.style.padding = "16px";
        
        const inattentionPercent = (trackerReport.inattentionRatio * 100).toFixed(1);
        const statusHtml = trackerReport.inattentionRatio >= 0.20 
            ? `<span style="color: var(--danger); font-weight: bold;">⚠️ Flagged for Cumulative Inattention</span>` 
            : `<span style="color: var(--success); font-weight: bold;">✅ Attention Check Passed</span>`;

        statsDiv.innerHTML = `
            <h3 style="margin-top: 0; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
                👁️ Eye Tracking & Attention Report
            </h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-bottom: 12px;">
                <div>
                    <div style="font-size: 0.8rem; color: var(--text-muted);">Total Off-Screen Time</div>
                    <div style="font-size: 1.25rem; font-weight: 600;">${(trackerReport.totalOffScreenMs / 1000).toFixed(1)}s</div>
                </div>
                <div>
                    <div style="font-size: 0.8rem; color: var(--text-muted);">Session Duration</div>
                    <div style="font-size: 1.25rem; font-weight: 600;">${(trackerReport.sessionDurationMs / 1000).toFixed(1)}s</div>
                </div>
                <div>
                    <div style="font-size: 0.8rem; color: var(--text-muted);">Inattention Ratio</div>
                    <div style="font-size: 1.25rem; font-weight: 600;">${inattentionPercent}%</div>
                </div>
            </div>
            <div style="padding-top: 12px; border-top: 1px solid var(--border); font-size: 0.9rem;">
                <strong>Status:</strong> ${statusHtml}
            </div>
        `;
        reportContent.appendChild(statsDiv);
    }

    // Scroll to report
    if (reportEl) reportEl.scrollIntoView({ behavior: "smooth" });
    showStatus("Interview complete! Your report is ready.", "success");
}

// ── Timer ─────────────────────────────────────────────────

function startCountdownTimer() {
    timeRemaining = interviewDurationMins * 60;
    updateTimerDisplay();

    interviewTimer = setInterval(() => {
        timeRemaining--;
        updateTimerDisplay();

        if (timeRemaining <= 0) {
            clearInterval(interviewTimer);
            endInterview();
        }
    }, 1000);
}

function updateTimerDisplay(forceVal) {
    const val = forceVal !== undefined ? forceVal : timeRemaining;
    const mins = Math.floor(val / 60);
    const secs = val % 60;
    const display = `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
    const timerEl = document.getElementById("timer");
    if (timerEl) {
        timerEl.textContent = display;
        if (val <= 60) timerEl.classList.add("timer-urgent");
        else timerEl.classList.remove("timer-urgent");
    }
}

// ── Question Timer ────────────────────────────────────────

function startQuestionTimer() {
    stopQuestionTimer(); // Clear any existing
    
    qTimeRemaining = Q_DURATION;
    const ring = document.getElementById("qTimerRing");
    if (ring) ring.style.display = "flex";
    
    updateQuestionTimerUI();

    qTimer = setInterval(() => {
        qTimeRemaining--;
        updateQuestionTimerUI();

        if (qTimeRemaining <= 0) {
            stopQuestionTimer();
            handleQuestionTimeout();
        }
    }, 1000);
}

function stopQuestionTimer() {
    if (qTimer) clearInterval(qTimer);
    qTimer = null;
    const ring = document.getElementById("qTimerRing");
    if (ring) ring.style.display = "none";
}

function updateQuestionTimerUI() {
    const textEl = document.getElementById("qTimerText");
    const circleEl = document.getElementById("qTimerCircle");
    const ringEl = document.getElementById("qTimerRing");

    if (textEl) textEl.textContent = qTimeRemaining;
    
    if (circleEl) {
        const offset = 113 - (113 * qTimeRemaining) / Q_DURATION;
        circleEl.style.strokeDashoffset = offset;
    }

    if (ringEl) {
        if (qTimeRemaining <= 30) ringEl.classList.add("q-timer-urgent");
        else ringEl.classList.remove("q-timer-urgent");
    }
}

async function handleQuestionTimeout() {
    showStatus("Time's up! Submitting your current answer...", "warning");
    
    // If recording, stop it. This will trigger sendAnswer via audio.js logic or we call it here.
    if (typeof stopRecording === "function") {
        const stopBtn = document.getElementById("stopBtn");
        if (stopBtn && !stopBtn.disabled) {
            stopRecording();
            return;
        }
    }
    
    // If not recording (maybe they never started), just send empty/default
    await sendAnswer("(No verbal answer provided - timed out)");
}

// ── Progress ──────────────────────────────────────────────

function updateProgress() {
    const progressEl = document.getElementById("questionProgress");
    if (progressEl) {
        progressEl.textContent = `Question ${questionCount} of ${MAX_QUESTIONS}`;
    }
    const barEl = document.getElementById("progressBar");
    if (barEl) {
        barEl.style.width = `${(questionCount / MAX_QUESTIONS) * 100}%`;
    }
}

function setQuestionStatus(state) {
    const indicator = document.getElementById("aiIndicator");
    if (!indicator) return;
    indicator.className = `ai-indicator ai-${state}`;
    const labels = {
        thinking: "🤔 AI is thinking…",
        speaking: "🗣️ AI is speaking…",
        waiting: "⏳ Waiting for your answer…",
        done: "✅ Interview complete",
        error: "❌ Error occurred"
    };
    indicator.textContent = labels[state] || "";
}

// Init on load
document.addEventListener("DOMContentLoaded", initInterview);