// audioDetector.js
const AUDIO_DETECTOR = (() => {
  const THRESHOLDS = {
    CALIBRATION_DURATION_MS: 5000,
    SPIKE_MULTIPLIER: 3,
    SPIKE_DURATION_MS: 500,
    VOICE_CONFIDENCE: 0.60,
    TYPING_CONFIDENCE: 0.50,
    TYPING_WINDOW_MS: 10000,
    TYPING_COUNT: 3,
    MUTE_DURATION_MS: 3000,
  };

  let audioCtx, analyserNode, audioTrack, recognizer;
  let baselineRMS = null;
  let isCalibrating = true;
  const calibrationSamples = [];
  let spikeStartTime = null;
  const typingEvents = []; // timestamps
  let muteCheckInterval = null;
  let muteStartTime = null;
  let onViolation = () => {};
  let onWarning = () => {};

  // ── RMS helpers ────────────────────────────────────────────────────────────

  function computeRMS(floatArray) {
    let sum = 0;
    for (let i = 0; i < floatArray.length; i++) sum += floatArray[i] ** 2;
    return Math.sqrt(sum / floatArray.length);
  }

  // ── Main analysis loop (called from AudioWorklet message) ─────────────────

  function analyseBuffer(floatArray) {
    const rms = computeRMS(floatArray);
    const now = Date.now();

    if (isCalibrating) {
      calibrationSamples.push(rms);
      return;
    }

    // Noise spike detection
    if (rms > baselineRMS * THRESHOLDS.SPIKE_MULTIPLIER) {
      if (!spikeStartTime) spikeStartTime = now;
      if (now - spikeStartTime >= THRESHOLDS.SPIKE_DURATION_MS) {
        onWarning('NOISE_SPIKE', {
          rms: rms.toFixed(4),
          baselineRMS: baselineRMS.toFixed(4),
          multiplier: (rms / baselineRMS).toFixed(2),
          durationMs: now - spikeStartTime,
        });
        spikeStartTime = null; // Cooldown — don't fire every frame
      }
    } else {
      spikeStartTime = null;
    }
  }

  // ── AudioWorklet processor (inlined as a Blob URL) ────────────────────────

  const WORKLET_CODE = `
    class RMSProcessor extends AudioWorkletProcessor {
      process(inputs) {
        const input = inputs[0];
        if (input.length > 0) {
          this.port.postMessage({ samples: Array.from(input[0]) });
        }
        return true;
      }
    }
    registerProcessor('rms-processor', RMSProcessor);
  `;

  async function init(stream, violationCb, warningCb) {
    onViolation = violationCb;
    onWarning = warningCb;
    isCalibrating = true;
    calibrationSamples.length = 0;
    spikeStartTime = null;
    typingEvents.length = 0;
    muteStartTime = null;

    audioCtx = new AudioContext();
    const source = audioCtx.createMediaStreamSource(stream);

    // Load worklet from blob to avoid CSP issues with external URLs
    const blob = new Blob([WORKLET_CODE], { type: 'application/javascript' });
    const workletUrl = URL.createObjectURL(blob);
    await audioCtx.audioWorklet.addModule(workletUrl);

    const workletNode = new AudioWorkletNode(audioCtx, 'rms-processor');
    workletNode.port.onmessage = (e) => analyseBuffer(new Float32Array(e.data.samples));
    source.connect(workletNode);

    // Calibrate for first 5 seconds
    setTimeout(() => {
      isCalibrating = false;
      const avg = calibrationSamples.reduce((a, b) => a + b, 0) / calibrationSamples.length;
      baselineRMS = Math.max(avg, 0.001); // Guard against silent environments
      console.log(`[AudioDetector] Baseline calibrated: RMS=${baselineRMS.toFixed(4)}`);
    }, THRESHOLDS.CALIBRATION_DURATION_MS);

    // Extract the audio track for mute monitoring
    audioTrack = stream.getAudioTracks()[0];
    startMuteMonitor();

    // Attempt to load TF.js speech classifier
    await loadSpeechClassifier();
  }

  // ── TF.js speech commands classifier ─────────────────────────────────────

  async function loadSpeechClassifier() {
    try {
      // Assumes window.speechCommands is loaded via <script> tag in the page
      if (typeof speechCommands === 'undefined') return;
      recognizer = speechCommands.create('BROWSER_FFT');
      await recognizer.ensureModelLoaded();

      recognizer.listen(handleClassification, {
        probabilityThreshold: THRESHOLDS.TYPING_CONFIDENCE,
        overlapFactor: 0.5,
      });
    } catch (err) {
      console.warn('[AudioDetector] Speech classifier unavailable:', err.message);
    }
  }

  function handleClassification(result) {
    const labels = recognizer.wordLabels();
    const now = Date.now();

    const speechIdx = labels.indexOf('speech') ?? labels.indexOf('yes'); // Fallback label
    const typingIdx = labels.indexOf('typing') ?? labels.indexOf('_unknown_');

    if (speechIdx >= 0 && result.scores[speechIdx] > THRESHOLDS.VOICE_CONFIDENCE) {
      onViolation('SECONDARY_VOICE', {
        severity: 'high',
        confidence: result.scores[speechIdx].toFixed(2),
        message: 'Secondary human voice detected with >' + (THRESHOLDS.VOICE_CONFIDENCE * 100) + '% confidence.',
      });
    }

    if (typingIdx >= 0 && result.scores[typingIdx] > THRESHOLDS.TYPING_CONFIDENCE) {
      typingEvents.push(now);
      // Prune events outside the rolling window
      const cutoff = now - THRESHOLDS.TYPING_WINDOW_MS;
      while (typingEvents.length && typingEvents[0] < cutoff) typingEvents.shift();

      if (typingEvents.length >= THRESHOLDS.TYPING_COUNT) {
        onWarning('KEYBOARD_TYPING', {
          eventCount: typingEvents.length,
          windowMs: THRESHOLDS.TYPING_WINDOW_MS,
          message: `≥${THRESHOLDS.TYPING_COUNT} keyboard events detected in a 10s window.`,
        });
        typingEvents.length = 0; // Reset window after soft warning
      }
    }
  }

  // ── Mute monitoring ────────────────────────────────────────────────────────

  function startMuteMonitor() {
    muteCheckInterval = setInterval(() => {
      if (!audioTrack) return;

      const isMuted = !audioTrack.enabled || audioTrack.muted;
      const now = Date.now();

      if (isMuted) {
        if (!muteStartTime) muteStartTime = now;
        if (now - muteStartTime >= THRESHOLDS.MUTE_DURATION_MS) {
          onViolation('UNEXPECTED_MUTE', {
            severity: 'critical',
            durationMs: now - muteStartTime,
            message: 'Audio track muted for >3s during active Q&A. Session paused.',
            action: 'PAUSE_SESSION',
          });
          muteStartTime = null; // Re-arm after firing
        }
      } else {
        muteStartTime = null;
      }
    }, 500); // 500ms poll — fine-grained enough without thrashing
  }

  function destroy() {
    recognizer?.stopListening();
    audioCtx?.close();
    clearInterval(muteCheckInterval);
  }

  return { init, destroy };
})();
