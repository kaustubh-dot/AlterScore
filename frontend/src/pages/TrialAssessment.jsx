import { useEffect, useRef, useState } from 'react';
import { ArrowLeft, ArrowRight, ShieldCheck } from 'lucide-react';
import Modal from '../components/ui/Modal';
import usePageTransition from '../hooks/usePageTransition';
import useSound from '../hooks/useSound';
import { saveTrialResult, scoreTrialAssessment, TRIAL_QUESTIONS } from '../lib/trialAssessment';

export default function TrialAssessment() {
  const { transitionTo } = usePageTransition();
  const { playClick, playSelect, playSuccess } = useSound();
  const [hasStarted, setHasStarted] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [validationMessage, setValidationMessage] = useState('');
  const [exitModalOpen, setExitModalOpen] = useState(false);
  const headingRef = useRef(null);
  const question = TRIAL_QUESTIONS[currentIndex];
  const isLast = currentIndex === TRIAL_QUESTIONS.length - 1;

  useEffect(() => {
    if (hasStarted) requestAnimationFrame(() => headingRef.current?.focus());
  }, [currentIndex, hasStarted]);

  const goForward = () => {
    if (!Number.isInteger(answers[question.id])) {
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
                <p>A five-question preview designed for a quick product evaluation. You will receive an immediate score, domain analysis, and answer guidance.</p>
                <div className="telemetry-specs">
                  <div className="spec-item"><ShieldCheck size={16} className="spec-icon" aria-hidden="true" /><span>About two minutes to complete</span></div>
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
            <span className="section-indicator">Quick trial · {question.domain}</span>
            <span className="question-counter">Question {currentIndex + 1} of {TRIAL_QUESTIONS.length}</span>
          </div>
          <section className="question-card slide-active" aria-labelledby="trial-question-heading">
            <h1 id="trial-question-heading" ref={headingRef} className="question-text" tabIndex="-1">{question.prompt}</h1>
            <fieldset className="choice-fieldset" aria-invalid={Boolean(validationMessage)} aria-describedby={validationMessage ? 'trial-validation' : 'trial-hint'}>
              <legend className="sr-only">{question.prompt}</legend>
              <div className="options-list" role="radiogroup" aria-label={question.prompt}>
                {question.choices.map((choice, index) => {
                  const selected = answers[question.id] === index;
                  return (
                    <label key={choice} className={`choice-option option-pill ${selected ? 'selected' : ''}`}>
                      <input className="choice-input" type="radio" name={question.id} checked={selected} onChange={() => { setAnswers((previous) => ({ ...previous, [question.id]: index })); setValidationMessage(''); playSelect(); }} />
                      <span>{choice}</span>
                    </label>
                  );
                })}
              </div>
            </fieldset>
            <p id="trial-hint" className="question-hint">Choose the strongest response.</p>
            {validationMessage && <p id="trial-validation" className="question-hint validation-message" role="alert">{validationMessage}</p>}
          </section>
          <div className="controls-row">
            <button type="button" onClick={() => { playClick(); setCurrentIndex((index) => index - 1); }} disabled={currentIndex === 0} className="btn btn-ghost"><ArrowLeft size={14} aria-hidden="true" /> Back</button>
            <button type="button" onClick={goForward} className="btn btn-primary"><span>{isLast ? 'View trial result' : 'Continue'}</span><ArrowRight size={14} aria-hidden="true" /></button>
          </div>
        </div>
      </div>
      <Modal isOpen={exitModalOpen} title="Exit Quick Trial?" message="Your responses will not be saved." confirmText="Exit" cancelText="Stay" onConfirm={exit} onCancel={() => setExitModalOpen(false)} />
    </main>
  );
}
