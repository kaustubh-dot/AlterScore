import { AlertCircle, ArrowRight, CheckCircle2, ExternalLink, GitBranch, Lightbulb, RefreshCw, ShieldCheck, Trash2 } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { getV2VerificationUrl } from '../lib/api';
import {
  clearSignedResult,
  getStoredSignedResult,
  isCurrentV2DetailedResult,
  isCurrentV2SignedResultSummary,
  isV2DetailedResult,
  saveSignedResult,
} from '../lib/assessmentV2';
import usePageTransition from '../hooks/usePageTransition';
import useSound from '../hooks/useSound';
import './Results.css';

const CONCEPT_LABELS = {
  cash_flow: 'Cash-flow arithmetic',
  simple_interest: 'Simple interest',
  borrowing_cost_comparison: 'Borrowing-cost comparison',
  discount_price: 'Discounted price',
  inflation_price: 'Inflation-adjusted price',
  due_date_shortfall: 'Due-date shortfall',
  repayment_total: 'Repayment total',
  emergency_buffer: 'Emergency buffer',
};

const DIMENSION_LABELS = {
  obligation_coverage: 'Obligation coverage',
  liquidity_retention: 'Liquidity retention',
  cost_efficiency: 'Cost efficiency',
  plan_feasibility: 'Plan feasibility',
};

const STATE_LABELS = {
  cash_available: 'Cash available',
  required_payments_due: 'Required payments due',
  required_payments_met: 'Required payments met',
  confirmed_inflows: 'Confirmed inflows',
  essential_expenses: 'Essential expenses',
  emergency_buffer: 'Emergency buffer',
  new_borrowing: 'New borrowing',
  borrowing_cost: 'Borrowing cost',
  avoidable_cost: 'Avoidable cost',
  late_payments: 'Late payments',
  unfunded_commitments: 'Unfunded commitments',
};

const STATE_FIELDS = Object.keys(STATE_LABELS);
const BEHAVIOR_VALUES = new Set(['Never', 'Rarely', 'Sometimes', 'Often', 'Always', 'Not applicable']);

function formatScore(value) {
  const number = Number(value);
  return Number.isFinite(number) ? number.toFixed(2) : '—';
}

function formatInteger(value) {
  return Number.isSafeInteger(value) ? value.toLocaleString('en-IN') : '—';
}

function formatDelta(value) {
  if (!Number.isSafeInteger(value)) return '—';
  if (value > 0) return `+${formatInteger(value)}`;
  return formatInteger(value);
}

function displayText(value) {
  return String(value);
}

function StateTable({ title, state, delta = false }) {
  return (
    <div className="state-table">
      <h4>{title}</h4>
      <dl>
        {STATE_FIELDS.map((field) => (
          <div key={field} className="state-row">
            <dt>{STATE_LABELS[field]}</dt>
            <dd className="font-mono">{delta ? formatDelta(state[field]) : formatInteger(state[field])}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

function getResultFromLocation(location) {
  const candidate = location.state?.result || location.state;
  if (isCurrentV2DetailedResult(candidate)) return candidate;
  if (isCurrentV2SignedResultSummary(candidate)) return candidate;
  return getStoredSignedResult();
}

function getBehaviorProfileFromLocation(location) {
  const candidate = location.state?.result;
  const profile = location.state?.behaviorProfile;
  if (!isCurrentV2DetailedResult(candidate) || !Array.isArray(profile) || profile.length !== 6) {
    return null;
  }
  const valid = profile.every((item) => (
    item !== null
    && typeof item === 'object'
    && Object.keys(item).length === 3
    && typeof item.presentation_id === 'string'
    && typeof item.prompt === 'string'
    && item.prompt.trim().length > 0
    && BEHAVIOR_VALUES.has(item.selected_value)
  ));
  return valid && new Set(profile.map((item) => item.presentation_id)).size === 6
    ? profile
    : null;
}

function ResultHeader({ children, eyebrow, title, id }) {
  return (
    <div className="results-section-header">
      <span className="section-eyebrow">{eyebrow}</span>
      <h2 id={id} className="results-section-title">{title}</h2>
      {children}
    </div>
  );
}

export default function Results() {
  const { transitionTo } = usePageTransition();
  const { playClick } = useSound();
  const location = useLocation();
  const [result, setResult] = useState(() => getResultFromLocation(location));
  const [behaviorProfile] = useState(() => getBehaviorProfileFromLocation(location));
  const detailed = isV2DetailedResult(result);
  const explanation = detailed ? result.explanation : null;

  useEffect(() => {
    if (isV2DetailedResult(result) || isCurrentV2SignedResultSummary(result)) saveSignedResult(result);
  }, [result]);

  useEffect(() => {
    if (!behaviorProfile || !result) return;
    const historyState = window.history.state;
    if (historyState && typeof historyState === 'object' && Object.hasOwn(historyState, 'usr')) {
      window.history.replaceState({ ...historyState, usr: result }, document.title);
    }
  }, [behaviorProfile, result]);

  const objectiveAnchors = useMemo(() => new Map(
    explanation?.objective_items.map((item, index) => [item.presentation_id, `objective-${index + 1}`]) || [],
  ), [explanation]);
  const scenarioAnchors = useMemo(() => new Map(
    explanation?.branching_scenarios.map((scenario, index) => [scenario.scenario_presentation_id, `scenario-${index + 1}`]) || [],
  ), [explanation]);

  const clearResult = () => {
    playClick();
    clearSignedResult();
    setResult(null);
  };

  if (!result) {
    return (
      <div className="results-layout results-empty-state">
        <div className="container results-empty-card" role="status" aria-live="polite">
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
  const formula = explanation?.formula;

  return (
    <div className="results-layout">
      <main className="results-container container" aria-labelledby="results-page-title">
        <header className="results-page-header">
          <div className="result-provenance" role="status">
            <ShieldCheck size={14} aria-hidden="true" />
            <span>Verified anonymous attempt · signed result retained for this session</span>
          </div>
          <span className="section-eyebrow">Financial readiness assessment</span>
          <h1 id="results-page-title">Your decision-readiness result</h1>
          <p>Read the score as a transparent educational rubric. The evidence below explains the issued questions and simulated decisions; it does not make a lending or repayment claim.</p>
        </header>

        <section className="score-reveal-section" aria-labelledby="score-heading">
          <div className="score-circle-wrapper" role="img" aria-label={`Financial Decision Index ${index} out of 100`}>
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
            <h2 className="summary-value font-mono">{formatScore(detailed ? result.objective_score : result.objective_score / 100)}</h2>
            <p>Objective domain display score.</p>
          </article>
          <article className="summary-card">
            <span className="card-kicker">Decision judgement</span>
            <h2 className="summary-value font-mono">{formatScore(detailed ? result.judgment_score : result.judgment_score / 100)}</h2>
            <p>Judgement domain display score.</p>
          </article>
        </section>

        {detailed && formula && (
          <section className="results-section formula-section" aria-labelledby="formula-heading">
            <ResultHeader eyebrow="Reconciliation" title="How the index is composed" id="formula-heading">
              <p className="section-intro">The displayed domain scores are shown alongside the exact contribution fractions returned by the scorer. No rounded display value is fed back into the calculation.</p>
            </ResultHeader>
            <div className="formula-waterfall" role="list" aria-label="Score contribution reconciliation">
              <article className="formula-step" role="listitem">
                <span className="formula-step-label">Objective contribution</span>
                <strong>{formatScore(formula.objective_score)} × {formula.objective_weight}</strong>
                <code>{formula.objective_contribution_exact}</code>
              </article>
              <ArrowRight className="formula-arrow" aria-hidden="true" />
              <article className="formula-step" role="listitem">
                <span className="formula-step-label">Judgement contribution</span>
                <strong>{formatScore(formula.judgment_score)} × {formula.judgment_weight}</strong>
                <code>{formula.judgment_contribution_exact}</code>
              </article>
              <ArrowRight className="formula-arrow" aria-hidden="true" />
              <article className="formula-step formula-step-final" role="listitem">
                <span className="formula-step-label">Final index</span>
                <strong>{formula.financial_decision_index} / 100</strong>
                <code>{formula.weighted_total_exact} → half-up integer</code>
              </article>
            </div>
            <div className="formula-footer">
              <span>Legacy illustration: <code>300 + floor((11 × {formula.financial_decision_index} + 1) ÷ 2)</code></span>
              <strong>{formula.legacy_demo_score}</strong>
            </div>
          </section>
        )}

        {detailed && explanation && (
          <>
            <section className="results-section recommendations-section" aria-labelledby="recommendations-heading">
              <ResultHeader eyebrow="Next attention" title="Deterministic recommendations" id="recommendations-heading">
                <p className="section-intro">Each recommendation is linked to a missed objective concept or a weak terminal simulation dimension. A maintenance note appears when no weakness evidence is present.</p>
              </ResultHeader>
              <ul className="recommendation-list">
                {explanation.recommendations.map((recommendation) => (
                  <li key={`${recommendation.evidence_type}-${recommendation.recommendation}`} className="recommendation-item">
                    <Lightbulb size={18} aria-hidden="true" />
                    <div>
                      <p>{recommendation.recommendation}</p>
                      {recommendation.evidence_ids.length > 0 && (
                        <div className="evidence-links" aria-label="Recommendation evidence">
                          {recommendation.evidence_ids.map((evidenceId) => {
                            const anchor = recommendation.evidence_type === 'objective'
                              ? objectiveAnchors.get(evidenceId)
                              : scenarioAnchors.get(evidenceId);
                            const ordinal = recommendation.evidence_type === 'objective'
                              ? explanation.objective_items.findIndex((item) => item.presentation_id === evidenceId) + 1
                              : explanation.branching_scenarios.findIndex((scenario) => scenario.scenario_presentation_id === evidenceId) + 1;
                            const evidenceLabel = recommendation.evidence_type === 'objective'
                              ? `Objective ${String(ordinal).padStart(2, '0')} evidence`
                              : `Simulation ${ordinal} evidence`;
                            return anchor ? (
                              <a key={evidenceId} href={`#${anchor}`} aria-label={`View ${evidenceLabel}`}>
                                View {evidenceLabel} <ArrowRight size={13} aria-hidden="true" />
                              </a>
                            ) : null;
                          })}
                        </div>
                      )}
                    </div>
                  </li>
                ))}
              </ul>
            </section>

            <section className="results-section" aria-labelledby="objectives-heading">
              <ResultHeader eyebrow="Worked evidence" title="Objective questions" id="objectives-heading">
                <p className="section-intro">These explanations use only the values issued for this attempt. The calculation text is evidence, not a new scoring rule.</p>
              </ResultHeader>
              <div className="explanation-stack">
                {explanation.objective_items.map((item, index) => (
                  <article className="evidence-card objective-card" id={`objective-${index + 1}`} key={item.presentation_id}>
                    <div className="evidence-card-header">
                      <div>
                        <span className="section-eyebrow">Objective {String(index + 1).padStart(2, '0')}</span>
                        <h3>{CONCEPT_LABELS[item.concept] || item.concept}</h3>
                      </div>
                      <span className={`result-chip ${item.is_correct ? 'result-chip-success' : 'result-chip-warning'}`}>
                        {item.is_correct ? <CheckCircle2 size={14} aria-hidden="true" /> : <AlertCircle size={14} aria-hidden="true" />}
                        {item.is_correct ? 'Correct' : 'Review'}
                      </span>
                    </div>
                    <div className="answer-pair">
                      <div><span>Submitted answer</span><strong className="font-mono">{formatInteger(item.submitted_answer)} INR</strong></div>
                      <div><span>Correct answer</span><strong className="font-mono">{formatInteger(item.correct_answer)} INR</strong></div>
                    </div>
                    <div className="issued-values-block">
                      <h4>Issued values</h4>
                      <dl className="issued-values-list">
                        {item.issued_values.map((issued) => (
                          <div key={issued.name}>
                            <dt>{issued.name.replaceAll('_', ' ')}</dt>
                            <dd className="font-mono">{formatInteger(issued.value)} <span>{issued.unit}</span></dd>
                          </div>
                        ))}
                      </dl>
                    </div>
                    <div className="worked-solution">
                      <span className="worked-label">Worked calculation</span>
                      <code>{displayText(item.worked_calculation)}</code>
                    </div>
                    <p className="evidence-explanation">{item.concept_explanation}</p>
                  </article>
                ))}
              </div>
            </section>

            <section className="results-section" aria-labelledby="judgement-heading">
              <ResultHeader eyebrow="Principle-level evidence" title="Decision judgement" id="judgement-heading">
                <p className="section-intro">The selected action is explained at the principle level. Hidden option-to-point tables and complete rubrics are never shown.</p>
              </ResultHeader>
              <div className="evidence-grid evidence-grid-four">
                {explanation.static_sjt_items.map((item, index) => (
                  <article className="evidence-card sjt-card" key={item.presentation_id}>
                    <span className="section-eyebrow">Scenario {String(index + 1).padStart(2, '0')}</span>
                    <h3>Your selected action</h3>
                    <p className="selected-action">{item.selected_option_label}</p>
                    <dl className="principle-list">
                      <div><dt>Principle</dt><dd>{item.principle}</dd></div>
                      <div><dt>Protects</dt><dd>{item.protects}</dd></div>
                      <div><dt>Risks</dt><dd>{item.risks}</dd></div>
                      <div><dt>Stronger principle</dt><dd>{item.stronger_principle}</dd></div>
                    </dl>
                  </article>
                ))}
              </div>
            </section>

            <section className="results-section" aria-labelledby="simulations-heading">
              <ResultHeader eyebrow="Decision replay" title="Branching simulations" id="simulations-heading">
                <p className="section-intro">Each replay shows the three issued stages, the selected action label, and the state change it produced. The calibrated score compares this path with the worst and best paths reachable in the same simulation; it is not a forecast of real-world outcomes.</p>
              </ResultHeader>
              <div className="explanation-stack">
                {explanation.branching_scenarios.map((scenario, index) => (
                  <article className="evidence-card scenario-card" id={`scenario-${index + 1}`} key={scenario.scenario_presentation_id}>
                    <div className="evidence-card-header">
                      <div>
                        <span className="section-eyebrow">Simulation {String(index + 1).padStart(2, '0')}</span>
                        <h3>Three-stage decision replay</h3>
                      </div>
                      <div className="scenario-score-block">
                        <span className="scenario-score font-mono">{formatScore(scenario.scenario_score)} / 100</span>
                        <small>Calibrated path score</small>
                      </div>
                    </div>
                    <StateTable title="Starting state" state={scenario.starting_state} />
                    <ol className="timeline-list">
                      {scenario.timeline.map((stage) => (
                        <li key={stage.stage_index} className="timeline-item">
                          <div className="timeline-marker" aria-hidden="true">{stage.stage_index}</div>
                          <div className="timeline-content">
                            <div className="timeline-header">
                              <div>
                                <span className="section-eyebrow">Stage {stage.stage_index}</span>
                                <h4>{stage.selected_option_label}</h4>
                              </div>
                              <GitBranch size={18} aria-hidden="true" />
                            </div>
                            <div className="transition-grid">
                              <StateTable title="Before" state={stage.state_before} />
                              <StateTable title="Change" state={stage.state_delta} delta />
                              <StateTable title="After" state={stage.state_after} />
                            </div>
                          </div>
                        </li>
                      ))}
                    </ol>
                    <div className="scenario-footer-grid">
                      <StateTable title="Terminal state" state={scenario.terminal_state} />
                      <div className="dimension-card">
                        <h4>Outcome dimensions</h4>
                        <dl className="dimension-list">
                          {Object.entries(DIMENSION_LABELS).map(([field, label]) => (
                            <div key={field}>
                              <dt>{label}</dt>
                              <dd className="font-mono">{formatScore(scenario.dimensions[field])}</dd>
                            </div>
                          ))}
                        </dl>
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            </section>
          </>
        )}

        {!detailed && (
          <section className="results-section detail-unavailable" aria-labelledby="detail-unavailable-heading">
            <ResultHeader eyebrow="Session recovery" title="Detailed evidence is not available" id="detail-unavailable-heading" />
            <p>This browser session retained the signed summary, but not the consumed question evidence. The verified score and limitations remain available below; a new attempt will produce a fresh explanation.</p>
            <button type="button" className="btn btn-primary" onClick={() => transitionTo('/assessment')}>
              Start a new assessment <ArrowRight size={16} aria-hidden="true" />
            </button>
          </section>
        )}

        {detailed && behaviorProfile && (
          <section className="results-section behavior-profile-section" aria-labelledby="behavior-profile-heading">
            <ResultHeader eyebrow="Unscored self-report" title="Your reflection profile" id="behavior-profile-heading">
              <p className="section-intro">These selections are displayed separately from the scored evidence. They are not compared with an answer key, do not affect either domain, and are removed from browser history after this view is opened.</p>
            </ResultHeader>
            <ol className="behavior-profile-list">
              {behaviorProfile.map((item) => (
                <li key={item.presentation_id}>
                  <span>{item.prompt}</span>
                  <strong>{item.selected_value}</strong>
                </li>
              ))}
            </ol>
            <p className="behavior-profile-note">Self-report can be mistaken or strategically chosen, so it is omitted from the signed verification record and the retained session result.</p>
          </section>
        )}

        <section className="limitations-card" aria-labelledby="limitations-heading">
          <ResultHeader eyebrow="Read carefully" title="What this result does not establish" id="limitations-heading" />
          <ul>
            {result.limitations.map((limitation) => <li key={limitation}>{limitation}</li>)}
          </ul>
        </section>

        <section className="verification-card" aria-labelledby="verification-heading">
          <ResultHeader eyebrow="Public proof" title="Verify the signed summary" id="verification-heading" />
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
