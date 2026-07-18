import { useEffect, useState, useRef } from 'react';
import './Preloader.css';

const STATUS_PHASES = [
  { max: 20, text: '01 / SYSTEM_BOOT_SEQUENCE' },
  { max: 45, text: '02 / SENSOR_MATRIX_ONLINE' },
  { max: 70, text: '03 / ANALYZING_COGNITIVE_BIAS' },
  { max: 90, text: '04 / COMPILING_TELEMETRY_PIPELINE' },
  { max: 99, text: '05 / RUNNING_STACKING_CALIBRATOR' },
  { max: 100, text: '06 / CONTEXT_CALIBRATED' },
];

export default function Preloader({ onComplete }) {
  const [count, setCount] = useState(0);
  const [statusText, setStatusText] = useState(STATUS_PHASES[0].text);
  const [isExiting, setIsExiting] = useState(false);
  const requestRef = useRef(null);
  const startTimeRef = useRef(null);

  useEffect(() => {
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reducedMotion) {
      onComplete();
      return undefined;
    }

    const duration = 2800;
    const animateCount = (timestamp) => {
      if (!startTimeRef.current) startTimeRef.current = timestamp;
      const progress = Math.min((timestamp - startTimeRef.current) / duration, 1);
      const easedProgress = progress < 0.3
        ? progress * 2
        : progress < 0.85
          ? 0.6 + (progress - 0.3) * 0.45
          : 0.8475 + (progress - 0.85) * 1.016;
      const currentCount = Math.min(Math.floor(easedProgress * 100), 100);
      setCount(currentCount);
      setStatusText((STATUS_PHASES.find((phase) => currentCount <= phase.max) || STATUS_PHASES[STATUS_PHASES.length - 1]).text);

      if (progress < 1 && currentCount < 100) {
        requestRef.current = requestAnimationFrame(animateCount);
        return;
      }

      setCount(100);
      setStatusText(STATUS_PHASES[STATUS_PHASES.length - 1].text);
      window.setTimeout(() => {
        setIsExiting(true);
        window.setTimeout(onComplete, 800);
      }, 300);
    };

    requestRef.current = requestAnimationFrame(animateCount);
    return () => {
      if (requestRef.current) cancelAnimationFrame(requestRef.current);
    };
  }, [onComplete]);

  const formattedCount = count.toString().padStart(2, '0');

  return (
    <div className={`preloader-overlay ${isExiting ? 'exit-slide' : ''}`} role="status" aria-live="polite">
      <div className="preloader-grid-lines" aria-hidden="true" />
      <div className="preloader-content">
        <div className="preloader-header"><span className="preloader-kicker">AlterScore // Behavioral Core</span></div>
        <div className="preloader-center">
          <div className="preloader-counter-wrapper" aria-label={`${count}% loaded`}>
            <span className="preloader-number">{formattedCount}</span>
            <span className="preloader-percent">%</span>
          </div>
        </div>
        <div className="preloader-footer"><span className="preloader-status">{statusText}</span></div>
      </div>
    </div>
  );
}
