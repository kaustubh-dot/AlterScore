import { useEffect, useState } from 'react';
import { AlertCircle, ExternalLink, RefreshCw, ShieldCheck, Trash2 } from 'lucide-react';
import { useLocation } from 'react-router-dom';
import { getV2VerificationUrl } from '../lib/api';
import {
  clearSignedResult,
  getStoredSignedResult,
  isCurrentV2SignedResultSummary,
  saveSignedResult,
} from '../lib/assessmentV2';
import usePageTransition from '../hooks/usePageTransition';
import useSound from '../hooks/useSound';
import './Results.css';

function formatDomainScore(value) {
  if (Number.isInteger(value)) return (value / 100).toFixed(2);
  const number = Number(value);
  return Number.isFinite(number) ? number.toFixed(2) : '—';
}

export default function Results() {
  const { transitionTo } = usePageTransition();
  const { playClick } = useSound();
  const location = useLocation();
  const [result, setResult] = useState(() => {
    const stateResult = location.state;
    if (isCurrentV2SignedResultSummary(stateResult)) return stateResult;
    return getStoredSignedResult();
  });

  useEffect(() => {
    if (isCurrentV2SignedResultSummary(result)) saveSignedResult(result);
  }, [result]);

  const clearResult = () => {
    playClick();
    clearSignedResult();
    setResult(null);
  };

  if (!result) {
    return (
      <div className="results-layout results-empty-state">
        <div className="container results-empty-card" role="status">
          <AlertCircle size={48} aria-hidden="true" />
          <h1>No current assessment result</h1>
          <p>The signed result is kept only in this browser session for up to 24 hours. Request a new assessment form to continue.</p>
          <button type="button" className="btn btn-primary" onClick={() => transitionTo('/assessment')}>
            Start assessment
          </button>
        </div>
      </div>
    );
  }

  const index = result.financial_decision_index;
  const ringOffset = 440 - (440 * index) / 100;
  const verificationUrl = getV2VerificationUrl(result.result_id);

  return (
    <div className="results-layout">
      <main className="results-container container">
        <div className="result-provenance" role="status">
          <ShieldCheck size={14} aria-hidden="true" />
          <span>Verified anonymous attempt · signed result retained for this session</span>
        </div>

        <section className="score-reveal-section" aria-labelledby="score-heading">
          <div className="score-circle-wrapper">
            <svg width="200" height="200" viewBox="0 0 200 200" className="score-svg" aria-hidden="true">
              <circle cx="100" cy="100" r="70" fill="transparent" className="score-track" />
              <circle cx="100" cy="100" r="70" fill="transparent" className="score-progress" style={{ strokeDashoffset: ringOffset }} />
            </svg>
            <div className="score-text-box">
              <span className="score-sub" id="score-heading">Financial Decision Index</span>
              <span className="score-num font-mono" aria-live="polite">{index}</span>
              <span className="score-band">0–100</span>
            </div>
          </div>
          <p className="score-disclaimer">An educational readiness rubric, not repayment probability, creditworthiness, approval, eligibility, pricing, or a loan offer.</p>
        </section>

        <section className="summary-grid" aria-label="Assessment summary">
          <article className="summary-card">
            <span className="card-kicker">Secondary illustration</span>
            <h2 className="summary-value font-mono">{result.legacy_demo_score}</h2>
            <p>Illustrative 300–850 transformation of the readiness index.</p>
          </article>
          <article className="summary-card">
            <span className="card-kicker">Integrity status</span>
            <h2 className="summary-value summary-status">{result.integrity_status}</h2>
            <p>The server issued, validated, consumed, and signed this anonymous attempt.</p>
          </article>
          <article className="summary-card">
            <span className="card-kicker">Financial knowledge</span>
            <h2 className="summary-value font-mono">{formatDomainScore(result.objective_score)}</h2>
            <p>Objective domain display score.</p>
          </article>
          <article className="summary-card">
            <span className="card-kicker">Decision judgement</span>
            <h2 className="summary-value font-mono">{formatDomainScore(result.judgment_score)}</h2>
            <p>Judgement domain display score.</p>
          </article>
        </section>

        <section className="limitations-card" aria-labelledby="limitations-heading">
          <div className="results-section-header">
            <span className="section-eyebrow">Read carefully</span>
            <h2 id="limitations-heading" className="results-section-title">What this result does not establish</h2>
          </div>
          <ul>
            {result.limitations.map((limitation) => <li key={limitation}>{limitation}</li>)}
          </ul>
        </section>

        <section className="verification-card" aria-labelledby="verification-heading">
          <div className="results-section-header">
            <span className="section-eyebrow">Public proof</span>
            <h2 id="verification-heading" className="results-section-title">Verify the signed summary</h2>
          </div>
          <p>The verification response contains only the redacted signed projection. It does not expose answers, behavior values, narrative text, or explanation detail.</p>
          <a className="verification-link" href={verificationUrl} target="_blank" rel="noreferrer">
            Open verification response <ExternalLink size={14} aria-hidden="true" />
          </a>
        </section>

        <div className="actions-row visible">
          <button type="button" className="btn btn-secondary" onClick={clearResult}>
            <Trash2 size={16} aria-hidden="true" /> Clear session result
          </button>
          <button type="button" className="btn btn-primary" onClick={() => { playClick(); transitionTo('/assessment'); }}>
            <RefreshCw size={16} aria-hidden="true" /> Take another assessment
          </button>
        </div>
      </main>
    </div>
  );
}
