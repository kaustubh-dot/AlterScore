import { useEffect, useRef, useState } from 'react';
import { Activity } from 'lucide-react';
import './Preloader.css';

const TICK_COUNT = 41;

function renderTicks() {
  return Array.from({ length: TICK_COUNT }, (_, index) => (
    <span className={`ruler-tick ${index % 5 === 0 ? 'major' : 'minor'}`} key={index} aria-hidden="true" />
  ));
}

export default function Preloader({ onComplete }) {
  const [percent, setPercent] = useState(0);
  const [opacity, setOpacity] = useState(1);
  const frameRef = useRef(null);
  const startRef = useRef(null);

  useEffect(() => {
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reducedMotion) {
      onComplete();
      return undefined;
    }

    const duration = 2500;
    const countDuration = 1900;
    const animate = (timestamp) => {
      if (startRef.current === null) startRef.current = timestamp;
      const elapsed = timestamp - startRef.current;
      setPercent(Math.min(Math.round((elapsed / countDuration) * 100), 100));
      setOpacity(elapsed > duration - 500 ? Math.max(0, 1 - (elapsed - (duration - 500)) / 500) : 1);
      if (elapsed < duration) frameRef.current = requestAnimationFrame(animate);
      else onComplete();
    };
    frameRef.current = requestAnimationFrame(animate);
    return () => {
      if (frameRef.current !== null) cancelAnimationFrame(frameRef.current);
    };
  }, [onComplete]);

  const translationPercent = -75 * (percent / 100);

  return (
    <div className="preloader-overlay" style={{ opacity }} role="status" aria-live="polite" aria-label={`Loading AlterScore ${percent}%`}>
      <div className="preloader-icon-container" aria-hidden="true"><Activity size={16} strokeWidth={1.5} className="preloader-icon" /><span className="preloader-brand">AlterScore</span></div>
      <div className="preloader-scale-viewport" aria-hidden="true">
        <div className="shadow-top" />
        <div className="preloader-scale-track" style={{ transform: `translate3d(0, ${translationPercent}%, 0)` }}><div className="ruler-segment">{renderTicks()}</div><div className="ruler-segment">{renderTicks()}</div></div>
        <div className="shadow-bot" />
      </div>
      <div className="preloader-percent-container" aria-hidden="true"><div className="percent-block"><span className="preloader-percent-num">{percent}</span><span className="preloader-percent-symbol">%</span></div></div>
    </div>
  );
}
