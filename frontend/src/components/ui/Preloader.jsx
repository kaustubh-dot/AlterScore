import React, { useEffect, useState, useRef } from 'react';
import './Preloader.css';

const STATUS_PHASES = [
  { max: 20, text: '01 / SYSTEM_BOOT_SEQUENCE' },
  { max: 45, text: '02 / SENSOR_MATRIX_ONLINE' },
  { max: 70, text: '03 / ANALYZING_COGNITIVE_BIAS' },
  { max: 90, text: '04 / COMPILING_TELEMETRY_PIPELINE' },
  { max: 99, text: '05 / RUNNING_STACKING_CALIBRATOR' },
  { max: 100, text: '06 / CONTEXT_CALIBRATED' }
];

export default function Preloader({ onComplete }) {
  const [count, setCount] = useState(0);
  const [statusText, setStatusText] = useState(STATUS_PHASES[0].text);
  const [isExiting, setIsExiting] = useState(false);
  const requestRef = useRef(null);
  const startTimeRef = useRef(null);

  useEffect(() => {
    const duration = 2800; // Simulated loading time in ms

    const animateCount = (timestamp) => {
      if (!startTimeRef.current) startTimeRef.current = timestamp;
      const elapsed = timestamp - startTimeRef.current;
      const progress = Math.min(elapsed / duration, 1);

      // Non-linear ease-in-out curve (fast start, slow crawl, quick finish)
      let easeProgress;
      if (progress < 0.3) {
        // Fast start
        easeProgress = progress * 2;
      } else if (progress < 0.85) {
        // Slow deliberation crawl
        easeProgress = 0.6 + (progress - 0.3) * 0.45;
      } else {
        // Rapid finalization
        easeProgress = 0.8475 + (progress - 0.85) * 1.016;
      }

      const currentCount = Math.min(Math.floor(easeProgress * 100), 100);
      setCount(currentCount);

      // Cycle status texts based on percentage
      const activePhase = STATUS_PHASES.find(p => currentCount <= p.max) || STATUS_PHASES[STATUS_PHASES.length - 1];
      setStatusText(activePhase.text);

      if (progress < 1 && currentCount < 100) {
        requestRef.current = requestAnimationFrame(animateCount);
      } else {
        // Hit 100% and initiate curtain slide-up
        setCount(100);
        setStatusText(STATUS_PHASES[STATUS_PHASES.length - 1].text);
        
        setTimeout(() => {
          setIsExiting(true);
          // Wait for CSS slide transition to complete before triggering main mount
          setTimeout(() => {
            onComplete();
          }, 800); // matches CSS exit animation time
        }, 300);
      }
    };

    requestRef.current = requestAnimationFrame(animateCount);

    return () => {
      if (requestRef.current) cancelAnimationFrame(requestRef.current);
    };
  }, [onComplete]);

  // Format count to 2 digits (e.g. 05) or 3 digits (100)
  const formattedCount = count.toString().padStart(2, '0');

  return (
    <div className={`preloader-overlay ${isExiting ? 'exit-slide' : ''}`}>
      {/* Visual Alignment grid marks */}
      <div className="preloader-grid-lines" />
      
      <div className="preloader-content">
        <div className="preloader-header">
          <span className="preloader-kicker">AlterScore // Behavioral Core</span>
        </div>

        <div className="preloader-center">
          <div className="preloader-counter-wrapper">
            <span className="preloader-number">{formattedCount}</span>
            <span className="preloader-percent">%</span>
          </div>
        </div>

        <div className="preloader-footer">
          <span className="preloader-status">{statusText}</span>
        </div>
      </div>
    </div>
  );
}
