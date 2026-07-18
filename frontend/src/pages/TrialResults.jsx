import { AlertCircle, ArrowRight, Lightbulb, RefreshCw, ShieldCheck } from 'lucide-react';
import usePageTransition from '../hooks/usePageTransition';
import useSound from '../hooks/useSound';
import { clearStoredTrialResult } from '../lib/trialAssessment';

const formatMoney = (value) => `₹${value.toLocaleString('en-IN')}`;

export default function TrialResults({ result }) {
  const { transitionTo } = usePageTransition();
  const { playClick } = useSound();
  const ringOffset = 440 - (440 * result.score) / 100;

  return (
    <div className="results-layout trial-results-layout">
      <main className="results-container container" aria-labelledby="trial-results-title">
        <header className="results-page-header">
          <div className="result-provenance trial-provenance" role="status"><AlertCircle size={14} aria-hidden="true" /><span>Quick trial · illustrative, unsigned result</span></div>
          <span className="section-eyebrow">Feasible-range branching preview</span>
          <h1 id="trial-results-title">Your trial readiness profile</h1>
          <p>This profile replays one connected financial state through all five decisions. Complete the full assessment for multiple simulations, objective items, and a server-signed result.</p>
        </header>

        <section className="score-reveal-section" aria-labelledby="trial-score-heading">
          <div className="score-circle-wrapper" role="img" aria-label={`Quick trial score ${result.score} out of 100`}>
            <svg width="200" height="200" viewBox="0 0 200 200" className="score-svg" aria-hidden="true"><circle cx="100" cy="100" r="70" className="score-track" /><circle cx="100" cy="100" r="70" className="score-progress" style={{ strokeDashoffset: ringOffset }} /></svg>
            <div className="score-text-box"><span className="score-sub" id="trial-score-heading">Readiness index</span><span className="score-num font-mono">{result.score}</span><span className="score-band">{result.band}</span></div>
          </div>
          <p className="score-disclaimer">{result.formula}. The terminal score is normalized between the weakest and strongest reachable paths; no decision carries a fixed mark.</p>
        </section>

        <section className="summary-grid" aria-label="Trial assessment summary">
          {result.domainScores.map((domain) => <article className="summary-card" key={domain.name}><span className="card-kicker">{domain.name}</span><h2 className="summary-value font-mono">{domain.score}</h2><p>Terminal state on a 0–100 scale.</p></article>)}
        </section>

        <section className="trial-terminal-state" aria-label="Terminal financial state">
          <div><span>Cash retained</span><strong>{formatMoney(result.terminalState.cashAvailable)}</strong></div>
          <div><span>Payment remaining</span><strong>{formatMoney(result.terminalState.paymentRemaining)}</strong></div>
          <div><span>Reserve retained</span><strong>{formatMoney(result.terminalState.emergencyBuffer)}</strong></div>
          <div><span>Cost accumulated</span><strong>{formatMoney(result.terminalState.costToDate)}</strong></div>
        </section>

        <section className="results-section recommendations-section" aria-labelledby="trial-focus-heading">
          <div className="results-section-header"><span className="section-eyebrow">Next steps</span><h2 id="trial-focus-heading" className="results-section-title">What to focus on next</h2><p className="section-intro">Guidance is prioritised by the weakest high-impact evidence, not by a simple wrong-answer count.</p></div>
          <ul className="recommendation-list">{result.recommendations.map((item) => <li key={item} className="recommendation-item"><Lightbulb size={18} aria-hidden="true" /><p>{item}</p></li>)}</ul>
        </section>

        <details className="results-disclosure">
          <summary><span><strong>Review the state replay</strong><small>See how each decision changed the state inherited by the next stage.</small></span><span className="disclosure-action" aria-hidden="true">View analysis</span></summary>
          <div className="disclosure-content explanation-stack">
            {result.feedback.map((item) => <article className="evidence-card objective-card" key={item.id}>
              <div className="evidence-card-header"><div><span className="section-eyebrow">Decision {String(item.number).padStart(2, '0')} · {item.pathLabel || item.domain}</span><h3>{item.prompt}</h3></div><span className={`result-chip ${item.quality >= 3 ? 'result-chip-success' : 'result-chip-warning'}`}>{item.quality >= 3 ? <ShieldCheck size={14} aria-hidden="true" /> : <AlertCircle size={14} aria-hidden="true" />}{item.rating}</span></div>
              <div className="answer-pair"><div><span>Your decision</span><strong>{item.selected}</strong></div><div><span>Best reachable move from this state</span><strong>{item.benchmark}</strong></div></div>
              <div className="trial-potential"><span>Reachable path potential retained</span><strong>{item.retainedPotential}%</strong></div>
              <dl className="trial-impact-list" aria-label="State changes caused by this decision">{item.impact.map((change) => <div key={change.label}><dt>{change.label}</dt><dd>{change.value}</dd></div>)}</dl>
              <dl className="principle-list"><div><dt>Principle</dt><dd>{item.principle}</dd></div><div><dt>Protects</dt><dd>{item.protects}</dd></div><div><dt>Trade-off or risk</dt><dd>{item.risks}</dd></div></dl>
              <p className="evidence-explanation">{item.analysis}</p>
            </article>)}
          </div>
        </details>

        <div className="actions-row visible">
          <button type="button" className="btn btn-secondary" onClick={() => { playClick(); transitionTo('/assessment?mode=trial'); }}><RefreshCw size={16} aria-hidden="true" /> Retry quick trial</button>
          <button type="button" className="btn btn-primary" onClick={() => { playClick(); clearStoredTrialResult(); transitionTo('/assessment'); }}>Take full assessment <ArrowRight size={16} aria-hidden="true" /></button>
        </div>
      </main>
    </div>
  );
}
