import { useState } from 'react';
import { AlertCircle, ArrowLeft, ExternalLink, RotateCcw, ShieldCheck, Trash2 } from 'lucide-react';
import { getV2VerificationUrl } from '../lib/api';
import {
  clearSignedResult,
  getStoredSignedResult,
} from '../lib/assessmentV2';
import usePageTransition from '../hooks/usePageTransition';
import useSound from '../hooks/useSound';
import './Dashboard.css';

function displayScore(value) {
  if (Number.isInteger(value)) return (value / 100).toFixed(2);
  return Number.isFinite(Number(value)) ? Number(value).toFixed(2) : '—';
}

export default function Dashboard() {
  const { transitionTo } = usePageTransition();
  const { playClick } = useSound();
  const [result, setResult] = useState(getStoredSignedResult);

  if (!result) {
    return (
      <div className="dashboard-blank-state">
        <div className="blank-state-card glass font-mono" role="status">
          <AlertCircle size={48} style={{ color: 'var(--accent-cyan)', marginBottom: '16px' }} aria-hidden="true" />
          <h1>No current session result</h1>
          <p className="dashboard-empty-copy">The anonymous signed summary is kept only in this browser session for up to 24 hours.</p>
          <button type="button" onClick={() => transitionTo('/assessment')} className="btn btn-primary">Start assessment</button>
        </div>
      </div>
    );
  }

  const verificationUrl = getV2VerificationUrl(result.result_id);
  const clearResult = () => {
    playClick();
    clearSignedResult();
    setResult(null);
  };

  return (
    <div className="dashboard-layout">
      <aside className="dashboard-sidebar">
        <div className="sidebar-title"><ShieldCheck size={18} style={{ color: 'var(--accent-cyan)' }} aria-hidden="true" /><span>AlterScore summary</span></div>
        <nav className="sidebar-menu" aria-label="Summary navigation">
          <button type="button" onClick={() => transitionTo('/')} className="sidebar-item btn-sidebar-action"><ArrowLeft size={16} aria-hidden="true" /><span>Home</span></button>
          <button type="button" onClick={() => transitionTo('/assessment')} className="sidebar-item btn-sidebar-action"><RotateCcw size={16} aria-hidden="true" /><span>New attempt</span></button>
          <div className="sidebar-item active"><ShieldCheck size={16} aria-hidden="true" /><span>Signed summary</span></div>
        </nav>
      </aside>

      <main className="dashboard-content">
        <header className="dashboard-header">
          <span className="dashboard-subtitle">Session-only summary</span>
          <h1 className="dashboard-title">Financial Decision Readiness</h1>
          <p className="dashboard-disclaimer">This educational index is not repayment probability, creditworthiness, approval, eligibility, pricing, or a loan offer.</p>
        </header>

        <div className="dashboard-grid">
          <section className="dashboard-hero-card glass" aria-labelledby="dashboard-index-heading">
            <div className="hero-card-left">
              <span className="section-eyebrow">Primary index</span>
              <h2 id="dashboard-index-heading" className="hero-card-title font-mono">{result.financial_decision_index} / 100</h2>
              <p className="hero-card-desc">A deterministic readiness-rubric result returned by the backend.</p>
            </div>
            <div className="hero-card-right dashboard-summary-mark" aria-hidden="true"><ShieldCheck size={56} /></div>
          </section>

          <div className="grid-6-6">
            <section className="dashboard-panel-card glass">
              <div className="panel-header"><h2 className="panel-title">Domain summaries</h2><span className="panel-badge">Display values</span></div>
              <div className="dashboard-metric-list">
                <div><span>Financial knowledge</span><strong className="font-mono">{displayScore(result.objective_score)}</strong></div>
                <div><span>Decision judgement</span><strong className="font-mono">{displayScore(result.judgment_score)}</strong></div>
                <div><span>Illustrative transformation</span><strong className="font-mono">{result.legacy_demo_score}</strong></div>
              </div>
            </section>
            <section className="dashboard-panel-card glass">
              <div className="panel-header"><h2 className="panel-title">Integrity</h2><span className="panel-badge">{result.integrity_status}</span></div>
              <p className="dashboard-panel-copy">The server issued this form, validated the response IDs, consumed the attempt once, and signed the result.</p>
              <a className="dashboard-verification-link" href={verificationUrl} target="_blank" rel="noreferrer">Verify signed summary <ExternalLink size={14} aria-hidden="true" /></a>
            </section>
          </div>

          <section className="dashboard-panel-card glass">
            <div className="panel-header"><h2 className="panel-title">Limitations</h2><span className="panel-badge">Public boundary</span></div>
            <ul className="dashboard-limitations">{result.limitations.map((limitation) => <li key={limitation}>{limitation}</li>)}</ul>
          </section>
        </div>

        <div className="dashboard-actions">
          <button type="button" className="btn btn-secondary" onClick={clearResult}><Trash2 size={16} aria-hidden="true" /> Clear session result</button>
          <button type="button" className="btn btn-primary" onClick={() => { playClick(); transitionTo('/assessment'); }}>Take another assessment</button>
        </div>
      </main>
    </div>
  );
}
