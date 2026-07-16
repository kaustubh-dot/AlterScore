import { ArrowLeft, ShieldAlert } from 'lucide-react';
import usePageTransition from '../hooks/usePageTransition';
import './Admin.css';

export default function Admin() {
  const { transitionTo } = usePageTransition();

  return (
    <div className="terminal-gate-container">
      <div className="terminal-gate-card">
        <div className="terminal-gate-header">
          <ShieldAlert size={16} className="gate-icon" />
          <span>ALTERSCORE SYNTHETIC DEMO</span>
        </div>
        <div className="terminal-gate-body font-mono">
          <p className="status-line">OPERATOR CONSOLE: DISABLED</p>
          <p className="status-line text-warning">NO CLIENT-SIDE MODEL METRICS OR LIVE LOG SIMULATIONS ARE SHOWN.</p>
          <p className="status-line">Manifest-backed reports are available only through the backend’s controlled internal interfaces.</p>
          <div className="gate-options">
            <button type="button" onClick={() => transitionTo('/')} className="btn-back-link font-mono">
              <ArrowLeft size={14} /> RETURN TO DEMO
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
