import { useEffect, useMemo, useState } from "react";

const FIRST_VISIT_MS = 2800;
const REPEAT_VISIT_MS = 650;
const SESSION_KEY = "alterscore_loader_seen";

const DIAGNOSTICS = [
  "CALIBRATING SIGNAL CORRIDOR",
  "MOUNTING BEHAVIORAL VECTOR FIELD",
  "CHECKING MODEL ARTIFACT STATUS",
  "SYNCING SCORE TIMELINE",
  "READY",
];

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

export default function LoadingScreen({ onComplete }) {
  const seenBefore = useMemo(() => {
    try {
      return window.sessionStorage.getItem(SESSION_KEY) === "true";
    } catch {
      return false;
    }
  }, []);
  const duration = seenBefore ? REPEAT_VISIT_MS : FIRST_VISIT_MS;
  const [progress, setProgress] = useState(0);
  const [lineIndex, setLineIndex] = useState(0);
  const [exiting, setExiting] = useState(false);

  useEffect(() => {
    let frame = 0;
    let doneTimer = 0;
    const startedAt = performance.now();

    function tick(now) {
      const elapsed = now - startedAt;
      const raw = clamp(elapsed / duration, 0, 1);
      const eased = 1 - Math.pow(1 - raw, 3);
      setProgress(Math.round(eased * 100));
      setLineIndex(Math.min(DIAGNOSTICS.length - 1, Math.floor(raw * DIAGNOSTICS.length)));

      if (raw < 1) {
        frame = window.requestAnimationFrame(tick);
      } else {
        setExiting(true);
        try {
          window.sessionStorage.setItem(SESSION_KEY, "true");
        } catch {
          // Non-critical: private browsing can reject sessionStorage.
        }
        doneTimer = window.setTimeout(onComplete, 520);
      }
    }

    frame = window.requestAnimationFrame(tick);
    return () => {
      window.cancelAnimationFrame(frame);
      window.clearTimeout(doneTimer);
    };
  }, [duration, onComplete]);

  return (
    <div className={`loading-screen loading-screen--cinematic${exiting ? " is-exiting" : ""}`}>
      <div className="loader-scanline" />
      <div className="loader-orbit" aria-hidden="true">
        <span />
        <span />
        <span />
      </div>

      <div className="loader-content loader-content--signal">
        <p className="loader-kicker">ALTERSCORE / BORROWER ENGINE</p>
        <h1 aria-label="Calibrating your signal">
          {"CALIBRATING YOUR SIGNAL".split("").map((char, index) => (
            <span key={`${char}-${index}`} style={{ animationDelay: `${index * 18}ms` }}>
              {char === " " ? "\u00A0" : char}
            </span>
          ))}
        </h1>

        <div className="loader-meter" aria-hidden="true">
          <i style={{ transform: `scaleX(${progress / 100})` }} />
        </div>

        <div className="loader-readout">
          <strong>{String(progress).padStart(3, "0")}</strong>
          <span>{DIAGNOSTICS[lineIndex]}</span>
        </div>
      </div>
    </div>
  );
}
