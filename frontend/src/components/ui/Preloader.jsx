import { useEffect } from 'react';
import { Activity } from 'lucide-react';
import './Preloader.css';

export default function Preloader({ onComplete }) {
  useEffect(() => {
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const timeout = window.setTimeout(onComplete, reducedMotion ? 0 : 900);
    return () => window.clearTimeout(timeout);
  }, [onComplete]);

  return (
    <div className="preloader-overlay" role="status" aria-live="polite">
      <div className="preloader-content">
        <div className="preloader-brand">
          <Activity size={18} aria-hidden="true" />
          <span>AlterScore</span>
        </div>
        <p>Preparing your assessment</p>
        <div className="preloader-progress" aria-hidden="true">
          <span />
        </div>
      </div>
    </div>
  );
}
