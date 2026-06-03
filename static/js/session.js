// session.js — connects both modules to the MediaPipe camera loop
async function startProctoring(videoElement) {
  // Reuse existing localStream if available, otherwise request fresh stream
  let stream = typeof localStream !== "undefined" ? localStream : null;
  if (!stream) {
      stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
      if (typeof localStream !== "undefined") {
          localStream = stream;
      }
  }
  videoElement.srcObject = stream;

  function handleViolation(type, detail) {
    console.error('[VIOLATION]', type, detail);
    // POST to your server — only metadata, never raw media
    fetch('/api/proctoring/event', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type, detail, timestamp: Date.now() }),
    });
    if (detail.action === 'PAUSE_SESSION') {
        if (typeof pauseSession === 'function') pauseSession(detail.message);
    }
  }

  function handleWarning(type, detail) {
    console.warn('[ADVISORY]', type, detail);
    fetch('/api/proctoring/event', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type, detail, timestamp: Date.now(), isAdvisory: true }),
    });
    if (typeof showStatus === 'function') showStatus(detail.message, "warning");
  }

  EYE_TRACKER.init(handleViolation, handleWarning);
  await AUDIO_DETECTOR.init(stream, handleViolation, handleWarning);

  // MediaPipe Face Mesh setup
  const faceMesh = new FaceMesh({ locateFile: (f) => `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${f}` });
  faceMesh.setOptions({ maxNumFaces: 4, refineLandmarks: true, minDetectionConfidence: 0.5, minTrackingConfidence: 0.5 });
  
  if (typeof window !== "undefined") {
      window.faceMesh = faceMesh;
  }

  faceMesh.onResults((results) => {
      EYE_TRACKER.onResults(results);
      // Handle auto-resume if paused and exactly 1 face is back
      const faceCount = results.multiFaceLandmarks?.length ?? 0;
      if (typeof isSessionPaused !== "undefined" && isSessionPaused && faceCount === 1) {
          if (typeof resumeSession === "function") resumeSession();
      }
  });

  // MediaPipe Camera Helper
  if (typeof Camera !== 'undefined') {
      const camera = new Camera(videoElement, {
        onFrame: async () => { 
          if (typeof interviewActive !== 'undefined' && interviewActive && typeof isSessionPaused !== 'undefined' && !isSessionPaused) {
              await faceMesh.send({ image: videoElement }); 
          }
        },
        width: 640, height: 480,
      });
      camera.start();
      window.proctoringCamera = camera;
  } else {
      let faceMeshActive = true;
      async function processFrame() {
          if (!faceMeshActive || (typeof interviewActive !== 'undefined' && !interviewActive)) return;
          if (videoElement.readyState >= 2 && !videoElement.paused && (typeof isSessionPaused !== 'undefined' && !isSessionPaused)) {
              try {
                  await faceMesh.send({ image: videoElement });
              } catch (e) {
                  console.error("FaceMesh processing error:", e);
              }
          }
          requestAnimationFrame(processFrame);
      }
      requestAnimationFrame(processFrame);
  }
}
