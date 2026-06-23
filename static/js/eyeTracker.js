// eyeTracker.js
const EYE_TRACKER = (() => {
  const THRESHOLDS = {
    GAZE_OFF_DEGREES: 30,
    GAZE_OFF_DURATION_MS: 2000,
    NO_FACE_DURATION_MS: 5000,
    MULTI_FACE_DURATION_MS: 3000,
    INATTENTION_RATIO: 0.20,
  };

  const state = {
    sessionStartTime: null,
    gazeOffStartTime: null,
    noFaceStartTime: null,
    multiFaceStartTime: null,
    totalOffScreenMs: 0,
    lastFrameTime: null,
    inattentionFlagged: false,
  };

  // Callbacks injected by the host app
  let onViolation = () => {};
  let onWarning = () => {};

  function init(violationCb, warningCb) {
    state.sessionStartTime = Date.now();
    state.lastFrameTime = Date.now();
    onViolation = violationCb;
    onWarning = warningCb;
    state.gazeOffStartTime = null;
    state.noFaceStartTime = null;
    state.multiFaceStartTime = null;
    state.totalOffScreenMs = 0;
    state.inattentionFlagged = false;
  }

  // Landmarks 234 (left cheek) and 454 (right cheek) form the face width.
  // Landmark 1 is the nose tip — used as the gaze reference origin.
  // Landmarks 468/473 are left/right iris centres.
  function calculateGazeAngleDegrees(landmarks) {
    const noseTip = landmarks[1];
    const leftCheek = landmarks[234];
    const rightCheek = landmarks[454];
    const leftIris = landmarks[468];
    const rightIris = landmarks[473];

    if (!leftIris || !rightIris) return 0;

    const faceWidth = Math.abs(rightCheek.x - leftCheek.x);
    if (faceWidth < 0.001) return 0;

    const irisCenter = {
      x: (leftIris.x + rightIris.x) / 2,
      y: (leftIris.y + rightIris.y) / 2,
    };

    // Offset from nose tip, normalised by face half-width
    const normalizedOffsetX = (irisCenter.x - noseTip.x) / (faceWidth / 2);
    const normalizedOffsetY = (irisCenter.y - noseTip.y) / (faceWidth / 2);

    // Convert to approximate degrees — atan2 gives radians
    const angleX = Math.atan2(normalizedOffsetX, 1) * (180 / Math.PI);
    const angleY = Math.atan2(normalizedOffsetY, 1) * (180 / Math.PI);

    return Math.sqrt(angleX ** 2 + angleY ** 2); // Euclidean angle from center
  }

  function onResults(results) {
    const now = Date.now();
    const frameDelta = state.lastFrameTime ? now - state.lastFrameTime : 16;
    state.lastFrameTime = now;

    const sessionDuration = now - state.sessionStartTime;
    const faceCount = results.multiFaceLandmarks?.length ?? 0;

    // ── Multiple faces ────────────────────────────────────────────────────────
    if (faceCount > 1) {
      if (!state.multiFaceStartTime) state.multiFaceStartTime = now;
      if (now - state.multiFaceStartTime >= THRESHOLDS.MULTI_FACE_DURATION_MS) {
        onViolation('MULTIPLE_FACES', {
          severity: 'critical',
          message: `${faceCount} faces detected for >${THRESHOLDS.MULTI_FACE_DURATION_MS / 1000}s. Session paused.`,
          action: 'PAUSE_SESSION',
        });
        state.multiFaceStartTime = null; // Reset after firing
      }
    } else {
      state.multiFaceStartTime = null;
    }

    // ── No face (confidence implicitly < 0.5 when MediaPipe returns 0 faces) ─
    if (faceCount === 0) {
      if (!state.noFaceStartTime) state.noFaceStartTime = now;
      if (now - state.noFaceStartTime >= THRESHOLDS.NO_FACE_DURATION_MS) {
        onViolation('NO_FACE', {
          severity: 'critical',
          message: `No face for >${THRESHOLDS.NO_FACE_DURATION_MS / 1000}s. Session paused.`,
          action: 'PAUSE_SESSION',
        });
        state.noFaceStartTime = null;
      }
      state.lastFrameTime = now;
      return; // No landmarks to process further
    }
    state.noFaceStartTime = null;

    // ── Gaze direction (only valid with exactly 1 face) ───────────────────────
    if (faceCount === 1) {
      const gazeAngle = calculateGazeAngleDegrees(results.multiFaceLandmarks[0]);
      const isGazeOff = gazeAngle > THRESHOLDS.GAZE_OFF_DEGREES;

      if (isGazeOff) {
        if (!state.gazeOffStartTime) state.gazeOffStartTime = now;
        state.totalOffScreenMs += frameDelta;

        if (now - state.gazeOffStartTime >= THRESHOLDS.GAZE_OFF_DURATION_MS) {
          onWarning('GAZE_OFF_SCREEN', {
            severity: 'advisory',
            message: `Gaze outside ${THRESHOLDS.GAZE_OFF_DEGREES}° cone for >2s (±15° accuracy — requires examiner review).`,
            gazeAngleDeg: gazeAngle.toFixed(1),
          });
          state.gazeOffStartTime = null; // Reset so next sustained violation fires again
        }
      } else {
        state.gazeOffStartTime = null;
      }
    }

    // ── Cumulative inattention ────────────────────────────────────────────────
    if (!state.inattentionFlagged && sessionDuration > 10000) {
      const ratio = state.totalOffScreenMs / sessionDuration;
      if (ratio >= THRESHOLDS.INATTENTION_RATIO) {
        state.inattentionFlagged = true; // Fire once — append to report
        onViolation('CUMULATIVE_INATTENTION', {
          severity: 'report',
          message: `Off-screen time exceeded 20% of session (${(ratio * 100).toFixed(1)}%).`,
          action: 'APPEND_TO_REPORT',
          totalOffScreenMs: state.totalOffScreenMs,
          sessionDurationMs: sessionDuration,
        });
      }
    }
  }

  function getReport() {
    const sessionDuration = Date.now() - state.sessionStartTime;
    return {
      totalOffScreenMs: state.totalOffScreenMs,
      sessionDurationMs: sessionDuration,
      inattentionRatio: (state.totalOffScreenMs / sessionDuration).toFixed(3),
    };
  }

  return { init, onResults, getReport };
})();
