import { AlertCircle, ArrowRight, CheckCircle2, Lightbulb, RefreshCw } from 'lucide-react';
import usePageTransition from '../hooks/usePageTransition';
import useSound from '../hooks/useSound';
import { clearStoredTrialResult } from '../lib/trialAssessment';

export default function TrialResults({ result }) {
  const { transitionTo } = usePageTransition();
  const { playClick } = useSound();
  const ringOffset = 440 - (440 * result.score) / 100;

  return (
    <div className="results-layout trial-results-layout">
      <main className="results-container container" aria-labelledby="trial-results-title">
        <header className="results-page-header">
          <div className="result-provenance trial-provenance" role="status"><AlertCircle size={14} aria-hidden="true" /><span>Quick trial · illustrative, unsigned result</span></div>
          <span className="section-eyebrow">Five-question product preview</span>
          <h1 id="trial-results-title">Your trial readiness snapshot</h1>
          <p>This short result highlights immediate strengths and review areas. Complete the full assessment for broader evidence and a server-signed score.</p>
        </header>

        <section className="score-reveal-section" aria-labelledby="trial-score-heading">
          <div className="score-circle-wrapper" role="img" aria-label={`Quick trial score ${result.score} out of 100`}>
            <svg width="200" height="200" viewBox="0 0 200 200" className="score-svg" aria-hidden="true"><circle cx="100" cy="100" r="70" className="score-track" /><circle cx="100" cy="100" r="70" className="score-progress" style={{ strokeDashoffset: ringOffset }} /></svg>
            <div className="score-text-box"><span className="score-sub" id="trial-score-heading">Trial score</span><span className="score-num font-mono">{result.score}</span><span className="score-band">{result.band}</span></div>
          </div>
          <p className="score-disclaimer">A five-question snapshot across cash flow, borrowing cost, buffers, and due-date decisions.</p>
        </section>

        <section className="summary-grid" aria-label="Trial assessment summary">
          <article className="summary-card"><span className="card-kicker">Questions correct</span><h2 className="summary-value font-mono">{result.correctCount} / {result.total}</h2><p>Your overall performance in this quick trial.</p></article>
          {result.domainScores.map((domain) => <article className="summary-card" key={domain.name}><span className="card-kicker">{domain.name}</span><h2 className="summary-value font-mono">{domain.score}%</h2><p>Performance within the trial questions for this domain.</p></article>)}
        </section>

        <section className="results-section recommendations-section" aria-labelledby="trial-focus-heading">
          <div className="results-section-header"><span className="section-eyebrow">Next steps</span><h2 id="trial-focus-heading" className="results-section-title">What to focus on next</h2><p className="section-intro">Guidance is linked to the trial responses that most need attention.</p></div>
          <ul className="recommendation-list">{result.recommendations.map((item) => <li key={item} className="recommendation-item"><Lightbulb size={18} aria-hidden="true" /><p>{item}</p></li>)}</ul>
        </section>

        <details className="results-disclosure">
          <summary><span><strong>Review all five responses</strong><small>See your answer, the stronger response, and why it matters.</small></span><span className="disclosure-action" aria-hidden="true">View analysis</span></summary>
          <div className="disclosure-content explanation-stack">
            {result.feedback.map((item) => <article className="evidence-card objective-card" key={item.id}>
              <div className="evidence-card-header"><div><span className="section-eyebrow">Question {String(item.number).padStart(2, '0')} · {item.domain}</span><h3>{item.prompt}</h3></div><span className={`result-chip ${item.isCorrect ? 'result-chip-success' : 'result-chip-warning'}`}>{item.isCorrect ? <CheckCircle2 size={14} aria-hidden="true" /> : <AlertCircle size={14} aria-hidden="true" />}{item.isCorrect ? 'Correct' : 'Review'}</span></div>
              <div className="answer-pair"><div><span>Your response</span><strong>{item.selected}</strong></div><div><span>Stronger response</span><strong>{item.correct}</strong></div></div>
              <p className="evidence-explanation">{item.explanation}</p>
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
