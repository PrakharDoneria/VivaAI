/**
 * VivaAI — Interview Analytics Dashboard
 * Fetches analytics data and renders interactive dashboard components.
 */

(function () {
    "use strict";

    // ─── Utility Functions ────────────────────────────────────

    /**
     * Animate a numeric counter from 0 to target value.
     */
    function animateCounter(element, target, duration = 1200, suffix = "") {
        const start = 0;
        const startTime = performance.now();

        function update(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            // Ease out cubic
            const eased = 1 - Math.pow(1 - progress, 3);
            const current = start + (target - start) * eased;

            if (target === null || target === undefined) {
                element.textContent = "N/A" + suffix;
                return;
            }

            if (Number.isInteger(target)) {
                element.textContent = Math.round(current) + suffix;
            } else {
                element.textContent = current.toFixed(1) + suffix;
            }

            if (progress < 1) {
                requestAnimationFrame(update);
            }
        }

        requestAnimationFrame(update);
    }

    /**
     * Format a date string to a readable format.
     */
    function formatDate(dateStr) {
        if (!dateStr) return "N/A";
        try {
            const d = new Date(dateStr);
            return d.toLocaleDateString("en-IN", {
                year: "numeric",
                month: "short",
                day: "numeric",
            });
        } catch {
            return dateStr;
        }
    }

    /**
     * Get CSS class for a score value.
     */
    function getScoreClass(score) {
        if (score === null || score === undefined) return "score-mid";
        if (score >= 7) return "score-high";
        if (score >= 5) return "score-mid";
        return "score-low";
    }

    /**
     * Get CSS class for a recommendation.
     */
    function getRecClass(rec) {
        if (!rec) return "rec-maybe";
        const lower = rec.toLowerCase().replace(/\s+/g, "-");
        if (lower === "strong-hire") return "rec-strong-hire";
        if (lower === "hire") return "rec-hire";
        if (lower === "maybe") return "rec-maybe";
        if (lower === "no-hire") return "rec-no-hire";
        return "rec-maybe";
    }

    // ─── Rendering Functions ──────────────────────────────────

    /**
     * Render summary stat cards with animated counters.
     */
    function renderStats(summary) {
        animateCounter(document.getElementById("totalInterviews"), summary.total_completed, 1000);
        animateCounter(document.getElementById("avgScore"), summary.average_score, 1200, "/10");
        animateCounter(document.getElementById("highScore"), summary.highest_score, 1000, "/10");
        animateCounter(document.getElementById("lowScore"), summary.lowest_score, 1000, "/10");
    }

    /**
     * Render the score progress line chart using Canvas API.
     */
    function renderProgressChart(progressData) {
        const canvas = document.getElementById("progressChart");
        if (!canvas || !progressData || progressData.length === 0) {
            const container = document.getElementById("chartContainer");
            if (container) {
                container.innerHTML =
                    '<div class="no-improvements"><div class="empty-icon">📈</div><p>Complete more interviews to see your score trend.</p></div>';
            }
            return;
        }

        const ctx = canvas.getContext("2d");
        const dpr = window.devicePixelRatio || 1;
        const rect = canvas.parentElement.getBoundingClientRect();
        canvas.width = rect.width * dpr;
        canvas.height = rect.height * dpr;
        canvas.style.width = rect.width + "px";
        canvas.style.height = rect.height + "px";
        ctx.scale(dpr, dpr);

        const W = rect.width;
        const H = rect.height;
        const pad = { top: 28, right: 24, bottom: 50, left: 48 };
        const chartW = W - pad.left - pad.right;
        const chartH = H - pad.top - pad.bottom;

        const scores = progressData.map((d) => d.score);
        const maxY = 10;
        const minY = 0;

        // Detect theme
        const isDark = document.documentElement.getAttribute("data-theme") !== "light";
        const textColor = isDark ? "#94a3b8" : "#475569";
        const gridColor = isDark ? "rgba(30,58,95,0.4)" : "rgba(148,163,184,0.25)";
        const accentColor = "#3b82f6";
        const gradientTop = isDark ? "rgba(59,130,246,0.25)" : "rgba(59,130,246,0.15)";
        const gradientBottom = isDark ? "rgba(59,130,246,0)" : "rgba(59,130,246,0)";

        // Clear
        ctx.clearRect(0, 0, W, H);

        // Grid lines + Y-axis labels
        ctx.font = "600 11px Inter, sans-serif";
        ctx.textAlign = "right";
        ctx.textBaseline = "middle";
        for (let i = 0; i <= 5; i++) {
            const val = (maxY / 5) * i;
            const y = pad.top + chartH - (val / maxY) * chartH;
            ctx.strokeStyle = gridColor;
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.moveTo(pad.left, y);
            ctx.lineTo(W - pad.right, y);
            ctx.stroke();

            ctx.fillStyle = textColor;
            ctx.fillText(val.toFixed(0), pad.left - 10, y);
        }

        // X-axis labels
        ctx.textAlign = "center";
        ctx.textBaseline = "top";
        const step = Math.max(1, Math.floor(progressData.length / 6));
        for (let i = 0; i < progressData.length; i += step) {
            const x = pad.left + (i / Math.max(1, progressData.length - 1)) * chartW;
            ctx.fillStyle = textColor;
            ctx.fillText(formatDate(progressData[i].date), x, H - pad.bottom + 12);
        }
        // Always show last label
        if (progressData.length > 1) {
            const lastX = pad.left + chartW;
            ctx.fillText(formatDate(progressData[progressData.length - 1].date), lastX, H - pad.bottom + 12);
        }

        // Plot points
        const points = progressData.map((d, i) => ({
            x: pad.left + (i / Math.max(1, progressData.length - 1)) * chartW,
            y: pad.top + chartH - ((d.score - minY) / (maxY - minY)) * chartH,
        }));

        // Area fill
        const gradient = ctx.createLinearGradient(0, pad.top, 0, pad.top + chartH);
        gradient.addColorStop(0, gradientTop);
        gradient.addColorStop(1, gradientBottom);

        ctx.beginPath();
        ctx.moveTo(points[0].x, pad.top + chartH);
        for (let i = 0; i < points.length; i++) {
            if (i === 0) {
                ctx.lineTo(points[i].x, points[i].y);
            } else {
                // Smooth curve
                const prev = points[i - 1];
                const cpx = (prev.x + points[i].x) / 2;
                ctx.bezierCurveTo(cpx, prev.y, cpx, points[i].y, points[i].x, points[i].y);
            }
        }
        ctx.lineTo(points[points.length - 1].x, pad.top + chartH);
        ctx.closePath();
        ctx.fillStyle = gradient;
        ctx.fill();

        // Line
        ctx.beginPath();
        for (let i = 0; i < points.length; i++) {
            if (i === 0) {
                ctx.moveTo(points[i].x, points[i].y);
            } else {
                const prev = points[i - 1];
                const cpx = (prev.x + points[i].x) / 2;
                ctx.bezierCurveTo(cpx, prev.y, cpx, points[i].y, points[i].x, points[i].y);
            }
        }
        ctx.strokeStyle = accentColor;
        ctx.lineWidth = 2.5;
        ctx.stroke();

        // Dots
        points.forEach((p, i) => {
            ctx.beginPath();
            ctx.arc(p.x, p.y, 5, 0, Math.PI * 2);
            ctx.fillStyle = isDark ? "#0d1526" : "#ffffff";
            ctx.fill();
            ctx.strokeStyle = accentColor;
            ctx.lineWidth = 2.5;
            ctx.stroke();
        });

        // Tooltip on hover
        canvas.onmousemove = function (e) {
            const rect = canvas.getBoundingClientRect();
            const mx = e.clientX - rect.left;
            const my = e.clientY - rect.top;

            let found = -1;
            for (let i = 0; i < points.length; i++) {
                const dx = mx - points[i].x;
                const dy = my - points[i].y;
                if (Math.sqrt(dx * dx + dy * dy) < 12) {
                    found = i;
                    break;
                }
            }

            canvas.style.cursor = found >= 0 ? "pointer" : "default";

            // Redraw to clear previous tooltip
            if (found >= 0) {
                const d = progressData[found];
                const px = points[found].x;
                const py = points[found].y;

                // Tooltip background
                const label = `${d.score}/10 — ${d.role}`;
                ctx.font = "600 12px Inter, sans-serif";
                const tw = ctx.measureText(label).width + 20;
                const th = 28;
                let tx = px - tw / 2;
                let ty = py - th - 12;
                if (tx < 0) tx = 4;
                if (tx + tw > W) tx = W - tw - 4;
                if (ty < 0) ty = py + 16;

                ctx.fillStyle = isDark ? "rgba(13,21,38,0.95)" : "rgba(255,255,255,0.95)";
                ctx.strokeStyle = accentColor;
                ctx.lineWidth = 1;
                ctx.beginPath();
                ctx.roundRect(tx, ty, tw, th, 8);
                ctx.fill();
                ctx.stroke();

                ctx.fillStyle = isDark ? "#f1f5f9" : "#0f172a";
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                ctx.fillText(label, tx + tw / 2, ty + th / 2);
            }
        };
    }

    /**
     * Render skill breakdown bars.
     */
    function renderSkills(skillAverages) {
        const container = document.getElementById("skillsContainer");
        if (!container) return;

        const skills = [
            { key: "technical", label: "Technical Knowledge", icon: "💻" },
            { key: "communication", label: "Communication", icon: "🗣️" },
            { key: "problem_solving", label: "Problem Solving", icon: "🧩" },
            { key: "confidence", label: "Confidence", icon: "💪" },
        ];

        let html = "";
        skills.forEach((skill) => {
            const score = skillAverages[skill.key];
            const hasScore = score !== null && score !== undefined && score !== 0;
            const displayScore = hasScore ? score.toFixed(1) : "N/A";
            const percent = hasScore ? (score / 10) * 100 : 0;
            
            html += `
                <div class="skill-item">
                    <div class="skill-header">
                        <span class="skill-name">${skill.icon} ${skill.label}</span>
                        <span class="skill-score">${displayScore}${hasScore ? "/10" : ""}</span>
                    </div>
                    <div class="skill-bar-track">
                        <div class="skill-bar-fill ${skill.key}" data-width="${percent}" style="width: 0%"></div>
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;

        // Animate bars after a short delay
        setTimeout(() => {
            container.querySelectorAll(".skill-bar-fill").forEach((bar) => {
                bar.style.width = bar.getAttribute("data-width") + "%";
            });
        }, 300);
    }

    /**
     * Render recommendations donut chart using Canvas API.
     */
    function renderRecommendations(recommendations, totalCompleted) {
        const container = document.getElementById("recContainer");
        if (!container) return;

        const recData = [
            { label: "Strong Hire", value: recommendations["Strong Hire"] || 0, color: "#10b981" },
            { label: "Hire", value: recommendations["Hire"] || 0, color: "#3b82f6" },
            { label: "Maybe", value: recommendations["Maybe"] || 0, color: "#f59e0b" },
            { label: "No Hire", value: recommendations["No Hire"] || 0, color: "#ef4444" },
        ];

        const total = recData.reduce((sum, d) => sum + d.value, 0);

        // Build HTML
        let legendHtml = "";
        recData.forEach((d) => {
            legendHtml += `
                <div class="rec-legend-item">
                    <div class="rec-legend-dot" style="background: ${d.color}"></div>
                    <span class="rec-legend-label">${d.label}</span>
                    <span class="rec-legend-count">${d.value}</span>
                </div>
            `;
        });

        container.innerHTML = `
            <div class="rec-chart-wrapper">
                <canvas id="recDonut"></canvas>
                <div class="rec-center-label">
                    <span class="rec-center-value">${total}</span>
                    <span class="rec-center-text">Total</span>
                </div>
            </div>
            <div class="rec-legend">${legendHtml}</div>
        `;

        // Draw donut
        const canvas = document.getElementById("recDonut");
        if (!canvas || total === 0) return;

        const ctx = canvas.getContext("2d");
        const dpr = window.devicePixelRatio || 1;
        const size = 180;
        canvas.width = size * dpr;
        canvas.height = size * dpr;
        canvas.style.width = size + "px";
        canvas.style.height = size + "px";
        ctx.scale(dpr, dpr);

        const cx = size / 2;
        const cy = size / 2;
        const outerR = size / 2 - 4;
        const innerR = outerR * 0.6;
        let startAngle = -Math.PI / 2;

        recData.forEach((d) => {
            if (d.value === 0) return;
            const sliceAngle = (d.value / total) * Math.PI * 2;
            const endAngle = startAngle + sliceAngle;

            ctx.beginPath();
            ctx.arc(cx, cy, outerR, startAngle, endAngle);
            ctx.arc(cx, cy, innerR, endAngle, startAngle, true);
            ctx.closePath();
            ctx.fillStyle = d.color;
            ctx.fill();

            // Small gap between segments
            ctx.strokeStyle = document.documentElement.getAttribute("data-theme") === "light"
                ? "#ffffff" : "#0d1526";
            ctx.lineWidth = 2;
            ctx.stroke();

            startAngle = endAngle;
        });
    }

    /**
     * Render improvement suggestions.
     */
    function renderImprovements(improvements) {
        const container = document.getElementById("improvementsContainer");
        if (!container) return;

        if (!improvements || improvements.length === 0) {
            container.innerHTML =
                '<div class="no-improvements"><div class="empty-icon">✨</div><p>Great job! No specific improvement areas identified yet. Keep practicing to get detailed insights.</p></div>';
            return;
        }

        const icons = ["🎯", "📝", "💡", "🔍", "📚", "⚡"];
        let html = "";
        improvements.forEach((text, i) => {
            html += `
                <div class="improvement-item" style="animation-delay: ${0.1 + i * 0.1}s">
                    <div class="improvement-icon">${icons[i % icons.length]}</div>
                    <span class="improvement-text">${text}</span>
                </div>
            `;
        });

        container.innerHTML = html;
    }

    /**
     * Render interview history table.
     */
    function renderHistory(history) {
        const body = document.getElementById("historyBody");
        const countBadge = document.getElementById("historyCount");
        if (!body) return;

        if (countBadge) {
            countBadge.textContent = `${history.length} session${history.length !== 1 ? "s" : ""}`;
        }

        if (!history || history.length === 0) {
            body.innerHTML =
                '<tr><td colspan="8" style="text-align:center; padding:32px; color:var(--text-muted);">No interview history yet.</td></tr>';
            return;
        }

        let html = "";
        history.forEach((entry, index) => {
            const scoreVal = entry.overall_score !== null && entry.overall_score !== undefined
                ? entry.overall_score : "N/A";
            const scoreClass = getScoreClass(entry.overall_score);

            const techVal = entry.technical !== null && entry.technical !== undefined ? entry.technical : "—";
            const commVal = entry.communication !== null && entry.communication !== undefined ? entry.communication : "—";
            const psVal = entry.problem_solving !== null && entry.problem_solving !== undefined ? entry.problem_solving : "—";

            const recClass = getRecClass(entry.recommendation);

            html += `
                <tr>
                    <td style="font-weight:600; color:var(--text-muted);">${index + 1}</td>
                    <td>${formatDate(entry.date)}</td>
                    <td><span class="role-badge">${entry.role}</span></td>
                    <td><span class="score-badge ${scoreClass}">${scoreVal !== "N/A" ? scoreVal + "/10" : scoreVal}</span></td>
                    <td><span class="score-badge ${getScoreClass(entry.technical)}">${techVal !== "—" ? techVal + "/10" : techVal}</span></td>
                    <td><span class="score-badge ${getScoreClass(entry.communication)}">${commVal !== "—" ? commVal + "/10" : commVal}</span></td>
                    <td><span class="score-badge ${getScoreClass(entry.problem_solving)}">${psVal !== "—" ? psVal + "/10" : psVal}</span></td>
                    <td><span class="rec-badge ${recClass}">${entry.recommendation || "N/A"}</span></td>
                </tr>
            `;
        });

        body.innerHTML = html;
    }

    // ─── Main Initialization ──────────────────────────────────

    async function initDashboard() {
        const loadingEl = document.getElementById("loadingState");
        const emptyEl = document.getElementById("emptyState");
        const contentEl = document.getElementById("dashboardContent");

        try {
            const res = await fetch("/api/analytics");
            if (!res.ok) throw new Error(`HTTP ${res.status}`);

            const data = await res.json();

            // Hide loading
            if (loadingEl) loadingEl.style.display = "none";

            // Check if there's data
            if (!data.summary || data.summary.total_completed === 0) {
                if (emptyEl) emptyEl.style.display = "block";
                return;
            }

            // Show dashboard
            if (contentEl) contentEl.style.display = "block";

            // Render all sections
            renderStats(data.summary);
            renderSkills(data.skill_averages || {});
            renderRecommendations(data.recommendations || {}, data.summary.total_completed);
            renderImprovements(data.improvements || []);
            renderHistory(data.history || []);

            // Render chart slightly delayed for animation
            setTimeout(() => {
                renderProgressChart(data.progress || []);
            }, 200);

        } catch (err) {
            console.error("Failed to load analytics:", err);
            if (loadingEl) {
                loadingEl.innerHTML = `
                    <div style="text-align:center;">
                        <div style="font-size:48px; margin-bottom:16px;">⚠️</div>
                        <p style="color:var(--text-secondary); font-size:1rem;">Failed to load analytics data.</p>
                        <p style="color:var(--text-muted); font-size:0.85rem; margin-top:8px;">${err.message}</p>
                        <button class="btn btn-primary" style="margin-top:20px;" onclick="location.reload()">🔄 Retry</button>
                    </div>
                `;
            }
        }
    }

    // Handle window resize for chart
    let resizeTimeout;
    window.addEventListener("resize", () => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            // Re-render chart on resize
            const canvas = document.getElementById("progressChart");
            if (canvas && canvas._progressData) {
                renderProgressChart(canvas._progressData);
            }
        }, 300);
    });

    // Boot
    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initDashboard);
    } else {
        initDashboard();
    }
})();
