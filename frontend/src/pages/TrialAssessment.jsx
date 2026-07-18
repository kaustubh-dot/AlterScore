import { useEffect, useRef, useState } from 'react';
import { ArrowLeft, ArrowRight, ShieldCheck } from 'lucide-react';
import Modal from '../components/ui/Modal';
import usePageTransition from '../hooks/usePageTransition';
import useSound from '../hooks/useSound';
import { clearStoredTrialResult, getTrialQuestion, saveTrialResult, scoreTrialAssessment, TRIAL_QUESTIONS } from '../lib/trialAssessment';

const formatMoney = (value) => `₹${value.toLocaleString('en-IN')}`;

export default function TrialAssessment() {
  const { transitionTo } = usePageTransition();
  const { playClick, playSelect, playSuccess } = useSound();
  const [hasStarted, setHasStarted] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [validationMessage, setValidationMessage] = useState('');
  const [exitModalOpen, setExitModalOpen] = useState(false);
  const headingRef = useRef(null);
  const question = getTrialQuestion(currentIndex, answers);
  const isLast = currentIndex === TRIAL_QUESTIONS.length - 1;

  useEffect(() => {
    clearStoredTrialResult();
  }, []);

  useEffect(() => {
    if (hasStarted) requestAnimationFrame(() => headingRef.current?.focus());
  }, [currentIndex, hasStarted]);

  const goForward = () => {
    if (!question.options.some((option) => option.id === answers[question.id])) {
      setValidationMessage('Choose one response to continue.');
      return;
    }
    playClick();
    if (!isLast) {
      setCurrentIndex((index) => index + 1);
      return;
    }
    playSuccess();
    const result = scoreTrialAssessment(answers);
    saveTrialResult(result);
    transitionTo('/results?mode=trial', { state: { trialResult: result } });
  };

  const selectAnswer = (optionId) => {
    setAnswers((previous) => {
      const next = { ...previous, [question.id]: optionId };
      TRIAL_QUESTIONS.slice(currentIndex + 1).forEach((item) => delete next[item.id]);
      return next;
    });
    setValidationMessage('');
    playSelect();
  };

  const exit = () => {
    playClick();
    setExitModalOpen(false);
    transitionTo('/');
  };

  if (!hasStarted) {
    return (
      <main className="assessment-layout">
        <button type="button" onClick={() => setExitModalOpen(true)} className="assessment-exit-btn">
          <ArrowLeft size={12} aria-hidden="true" /> Exit
        </button>
        <div className="assessment-container container">
          <div className="assessment-wrapper">
            <div className="consent-card animate-fade-up">
              <div className="consent-icon"><ShieldCheck size={32} aria-hidden="true" /></div>
              <h1 className="consent-title">Financial Readiness Quick Trial</h1>
              <div className="consent-text">
                <p>A five-stage financial simulation. Every choice changes the cash, obligation, reserve, cost, and commitment state used by every stage that follows.</p>
                <div className="telemetry-specs">
                  <div className="spec-item"><ShieldCheck size={16} className="spec-icon" aria-hidden="true" /><span>About three minutes to complete</span></div>
                  <div className="spec-item"><ShieldCheck size={16} className="spec-icon" aria-hidden="true" /><span>All 243 reachable decision paths are calibrated, not marked question by question</span></div>
                  <div className="spec-item"><ShieldCheck size={16} className="spec-icon" aria-hidden="true" /><span>No identity, device, or credit-history data is used</span></div>
                  <div className="spec-item"><ShieldCheck size={16} className="spec-icon" aria-hidden="true" /><span>Preview result only; server-signed scoring is reserved for the full assessment</span></div>
                </div>
              </div>
              <button type="button" onClick={() => { playClick(); setHasStarted(true); }} className="btn btn-primary" style={{ width: '100%' }}>
                Begin quick trial <ArrowRight size={16} aria-hidden="true" />
              </button>
            </div>
          </div>
        </div>
        <Modal isOpen={exitModalOpen} title="Exit Quick Trial?" message="Your responses will not be saved." confirmText="Exit" cancelText="Stay" onConfirm={exit} onCancel={() => setExitModalOpen(false)} />
      </main>
    );
  }

  const progress = ((currentIndex + 1) / TRIAL_QUESTIONS.length) * 100;
  return (
    <main className="assessment-layout">
      <div className="progress-rail" style={{ width: `${progress}%` }} role="progressbar" aria-valuenow={currentIndex + 1} aria-valuemin="1" aria-valuemax={TRIAL_QUESTIONS.length} aria-label="Quick trial progress" />
      <button type="button" onClick={() => setExitModalOpen(true)} className="assessment-exit-btn"><ArrowLeft size={12} aria-hidden="true" /> Exit</button>
      <div className="assessment-container container">
        <div className="assessment-wrapper">
          <div className="assessment-header" aria-live="polite">
            <span className="section-indicator">Quick trial · {question.label}</span>
            <span className="question-counter">Question {currentIndex + 1} of {TRIAL_QUESTIONS.length}</span>
          </div>
          <section className="question-card slide-active" aria-labelledby="trial-question-heading">
            <h1 id="trial-question-heading" ref={headingRef} className="question-text" tabIndex="-1">{question.prompt}</h1>
            <dl className="trial-state-grid" aria-label="Financial state entering this decision">
              <div><dt>Cash</dt><dd>{formatMoney(question.state.cashAvailable)}</dd></div>
              <div><dt>Payment left</dt><dd>{formatMoney(question.state.paymentRemaining)}</dd></div>
              <div><dt>Reserve</dt><dd>{formatMoney(question.state.emergencyBuffer)}</dd></div>
              <div><dt>Cost to date</dt><dd>{formatMoney(question.state.costToDate)}</dd></div>
            </dl>
            <fieldset className="choice-fieldset" aria-invalid={Boolean(validationMessage)} aria-describedby={validationMessage ? 'trial-validation' : 'trial-hint'}>
              <legend className="sr-only">{question.prompt}</legend>
              <div className="options-list" role="radiogroup" aria-label={question.prompt}>
                {question.options.map((option) => {
                  const selected = answers[question.id] === option.id;
                  return (
                    <label key={option.id} className={`choice-option option-pill ${selected ? 'selected' : ''}`}>
                      <input className="choice-input" type="radio" name={question.id} checked={selected} onChange={() => selectAnswer(option.id)} />
                      <span>{option.label}</span>
                    </label>
                  );
                })}
              </div>
            </fieldset>
            <p id="trial-hint" className="question-hint">There is no isolated mark for this choice. Its state transition changes every remaining decision and the terminal profile.</p>
            {validationMessage && <p id="trial-validation" className="question-hint validation-message" role="alert">{validationMessage}</p>}
          </section>
          <div className="controls-row">
            <button type="button" onClick={() => { playClick(); setCurrentIndex((index) => index - 1); }} disabled={currentIndex === 0} className="btn btn-ghost"><ArrowLeft size={14} aria-hidden="true" /> Back</button>
            <button type="button" onClick={goForward} className="btn btn-primary"><span>{isLast ? 'Calculate profile' : 'Continue'}</span><ArrowRight size={14} aria-hidden="true" /></button>
          </div>
        </div>
      </div>
      <Modal isOpen={exitModalOpen} title="Exit Quick Trial?" message="Your responses will not be saved." confirmText="Exit" cancelText="Stay" onConfirm={exit} onCancel={() => setExitModalOpen(false)} />
    </main>
  );
}
