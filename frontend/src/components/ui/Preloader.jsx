import { useEffect, useState, useRef } from 'react';
import { Activity } from 'lucide-react';
import './Preloader.css';

export default function Preloader({ onComplete }) {
  const [percent, setPercent] = useState(0);
  const [blur, setBlur] = useState(30);
  const [opacity, setOpacity] = useState(1);
  const startTimeRef = useRef(null);
  const requestRef = useRef(null);

  useEffect(() => {
    const duration = 2500; // total duration: 2.5s
    const activeDuration = 1900; // counter/ruler active time: 1.9s

    const step = (timestamp) => {
      if (!startTimeRef.current) startTimeRef.current = timestamp;
      const elapsed = timestamp - startTimeRef.current;
      const progress = Math.min(elapsed / duration, 1);

      // 1) Blur animation: 30px -> 0px over total duration
      const currentBlur = 30 * (1 - progress);
      setBlur(currentBlur);

      // 2) Opacity fade out in the last 500ms (from 2.0s to 2.5s)
      if (elapsed >= 2000) {
        const fadeProgress = (elapsed - 2000) / 500;
        setOpacity(1 - Math.min(fadeProgress, 1));
      }

      // 3) Percent progress (0 to 100 in 1.9s)
      const countProgress = Math.min(elapsed / activeDuration, 1);
      setPercent(Math.round(countProgress * 100));

      if (elapsed < duration) {
        requestRef.current = requestAnimationFrame(step);
      } else {
        onComplete();
      }
    };

    requestRef.current = requestAnimationFrame(step);
    return () => {
      if (requestRef.current) cancelAnimationFrame(requestRef.current);
    };
  }, [onComplete]);

  // Translate scale from 0% to -75% based on percent progress (max 100)
  const translationPercent = -75 * (percent / 100);

  // Generate tick marks (41 ticks, spacing 20px apart to fill 800px)
  const renderTicks = () => {
    return Array.from({ length: 41 }).map((_, i) => {
      const isMajor = i % 5 === 0;
      return (
        <div 
          key={i} 
          className={`ruler-tick ${isMajor ? 'major' : 'minor'}`}
        />
      );
    });
  };

  return (
    <div 
      className="preloader-overlay"
      style={{
        backdropFilter: `blur(${blur}px)`,
        WebkitBackdropFilter: `blur(${blur}px)`,
        opacity: opacity,
      }}
    >
      {/* Left Aligned: Brand Logo Icon */}
      <div className="preloader-icon-container">
        <Activity className="preloader-icon" size={18} />
        <span className="preloader-brand">AlterScore</span>
      </div>

      {/* Center Aligned: Vertical Ruler Tape viewport */}
      <div className="preloader-scale-viewport">
        <div className="shadow-top" />
        <div 
          className="preloader-scale-track"
          style={{ transform: `translate3d(0, ${translationPercent}%, 0)` }}
        >
          <div className="ruler-segment">{renderTicks()}</div>
          <div className="ruler-segment">{renderTicks()}</div>
        </div>
        <div className="shadow-bot" />
      </div>

      {/* Right Aligned: Percentage Text Counter */}
      <div className="preloader-percent-container">
        <div className="percent-block">
          <span className="preloader-percent-num">{percent}</span>
          <span className="preloader-percent-symbol">%</span>
        </div>
      </div>
    </div>
  );
}
