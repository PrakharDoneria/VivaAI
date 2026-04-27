// interview.js — AI interview logic

let questionHistory = [];
let currentQuestion = "";
let questionCount = 0;
let interviewActive = false;
let interviewTimer = null;
let timeRemaining = 0;
let roleValue = "Software Developer";

// Room token — loaded once the page knows its roomId
function getRoomToken() {
    if (typeof roomId === "undefined") return null;
    return sessionStorage.getItem(`room_token_${roomId}`) || null;
}

function authHeaders() {
    const token = getRoomToken();
    const headers = { "Content-Type": "application/json" };
    if (token) headers["X-Room-Token"] = token;
    return headers;
}

const MAX_QUESTIONS = 6;
const DURATION_SECONDS = 600; // 10 minutes

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

// ── Init ─────────────────────────────────────────────────

function initInterview() {
    // Read room meta from page
    const metaRole = document.getElementById("metaRole");
    if (metaRole) roleValue = metaRole.value || roleValue;

    // Set up button states
    const stopBtn = document.getElementById("stopBtn");
    if (stopBtn) stopBtn.disabled = true;

    updateProgress();
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

    interviewActive = true;

    const startBtn = document.getElementById("startBtn");
    if (startBtn) { startBtn.disabled = true; startBtn.textContent = "Interview in progress…"; }

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
            headers: authHeaders(),
            body: JSON.stringify({
                role: roleValue,
                answer: answerText,
                question_history: questionHistory,
                room_token: getRoomToken()
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
            });
        } else {
            setQuestionStatus("waiting");
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
    clearInterval(interviewTimer);

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
            headers: authHeaders(),
            body: JSON.stringify({
                role: roleValue,
                qa_history: questionHistory,
                room_id: typeof roomId !== "undefined" ? roomId : null,
                room_token: getRoomToken()
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
    }

    // Scroll to report
    if (reportEl) reportEl.scrollIntoView({ behavior: "smooth" });
    showStatus("Interview complete! Your report is ready.", "success");
}

// ── Timer ─────────────────────────────────────────────────

function startCountdownTimer() {
    timeRemaining = DURATION_SECONDS;
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

function updateTimerDisplay() {
    const mins = Math.floor(timeRemaining / 60);
    const secs = timeRemaining % 60;
    const display = `${String(mins).padStart(2, "0")}:${String(secs).padStart(2, "0")}`;
    const timerEl = document.getElementById("timer");
    if (timerEl) {
        timerEl.textContent = display;
        if (timeRemaining <= 60) timerEl.classList.add("timer-urgent");
    }
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