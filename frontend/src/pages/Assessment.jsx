import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { ArrowLeft, ArrowRight, RefreshCw, ShieldCheck } from 'lucide-react';
import Modal from '../components/ui/Modal';
import TextReveal from '../components/animation/TextReveal';
import SignalCanvas from '../components/hero/SignalCanvas';
import { fetchV2AssessmentForm } from '../lib/api';
import {
  buildScoreSubmission,
  getAssessmentSteps,
  getStepLabel,
  isV2ScoreResponse,
  saveSignedResult,
  toV2DetailedResult,
  validateAllResponses,
  validateFormResponse,
  validateStepResponse,
} from '../lib/assessmentV2';
import {
  formatApiError,
  isCancellationError,
} from '../utils/apiErrors';
import Processing from './Processing';
import usePageTransition from '../hooks/usePageTransition';
import useSound from '../hooks/useSound';
import './Assessment.css';

function getFormErrorMessage(error) {
  if (error?.code === 'unsupported_version' || error?.code === 'invalid_form') {
    return error.message;
  }
  return formatApiError(error, 'The assessment form could not be loaded.');
}

function makeFormError(message) {
  const error = new Error(message);
  error.code = message.includes('version') ? 'unsupported_version' : 'invalid_form';
  return error;
}

function buildBehaviorProfileDisplay(form, scoreData) {
  const promptById = new Map(
    form.behavior_profile_items.map((item) => [item.presentation_id, item.prompt]),
  );
  const profile = scoreData.behavior_profile.map((selection) => ({
    presentation_id: selection.presentation_id,
    prompt: promptById.get(selection.presentation_id),
    selected_value: selection.selected_value,
  }));
  return profile.every((selection) => typeof selection.prompt === 'string')
    ? profile
    : null;
}

export default function Assessment() {
  const { transitionTo } = usePageTransition();
  const { playClick, playSelect, playSuccess } = useSound();
  const [hasStarted, setHasStarted] = useState(false);
  const [form, setForm] = useState(null);
  const [formStatus, setFormStatus] = useState('idle');
  const [formError, setFormError] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [direction, setDirection] = useState('active');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submissionPayload, setSubmissionPayload] = useState(null);
  const [resetModalOpen, setResetModalOpen] = useState(false);
  const [exitModalOpen, setExitModalOpen] = useState(false);
  const [validationMessage, setValidationMessage] = useState('');

  const formRequestRef = useRef(null);
  const formAbortRef = useRef(null);
  const isMountedRef = useRef(true);
  const questionHeadingRef = useRef(null);
  const actionLockRef = useRef(false);

  const steps = useMemo(() => getAssessmentSteps(form), [form]);
  const currentStep = steps[currentIndex];
  const isFirst = currentIndex === 0;
  const isLast = currentIndex === steps.length - 1;
  const currentAnswer = currentStep ? answers[currentStep.id] : undefined;

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
      formAbortRef.current?.abort();
    };
  }, []);

  useEffect(() => {
    if (!hasStarted || formStatus !== 'ready' || isSubmitting) return;
    window.requestAnimationFrame(() => questionHeadingRef.current?.focus());
  }, [currentIndex, formStatus, hasStarted, isSubmitting]);

  const loadForm = useCallback(() => {
    if (formRequestRef.current) return formRequestRef.current;

    const controller = new AbortController();
    formAbortRef.current = controller;
    setFormStatus('loading');
    setFormError('');

    const request = fetchV2AssessmentForm({ signal: controller.signal })
      .then(({ data }) => {
        const validationError = validateFormResponse(data);
        if (validationError) throw makeFormError(validationError);
        if (isMountedRef.current) {
          setForm(data);
          setAnswers({});
          setCurrentIndex(0);
          setValidationMessage('');
          setFormStatus('ready');
        }
        return data;
      })
      .catch((error) => {
        if (!isCancellationError(error) && isMountedRef.current) {
          setForm(null);
          setFormStatus('error');
          setFormError(getFormErrorMessage(error));
        }
        throw error;
      })
      .finally(() => {
        if (formRequestRef.current === request) formRequestRef.current = null;
        if (formAbortRef.current === controller) formAbortRef.current = null;
      });

    formRequestRef.current = request;
    return request;
  }, []);

  const handleBegin = useCallback(() => {
    playClick();
    setHasStarted(true);
    loadForm().catch(() => {});
  }, [loadForm, playClick]);

  const handleFreshAttempt = useCallback(() => {
    actionLockRef.current = false;
    setIsSubmitting(false);
    setSubmissionPayload(null);
    setForm(null);
    setAnswers({});
    setCurrentIndex(0);
    setValidationMessage('');
    setHasStarted(true);
    loadForm().catch(() => {});
  }, [loadForm]);

  const handleStandardAnswer = useCallback((value) => {
    if (!currentStep) return;
    const nextValue = currentStep.kind === 'narrative'
      ? String(value).slice(0, currentStep.item.max_length)
      : value;
    setAnswers((previous) => ({ ...previous, [currentStep.id]: nextValue }));
    setValidationMessage('');
  }, [currentStep]);

  const handleChoiceAnswer = useCallback((optionId) => {
    if (!currentStep) return;
    setAnswers((previous) => ({ ...previous, [currentStep.id]: optionId }));
    setValidationMessage('');
    playSelect();
  }, [currentStep, playSelect]);

  const goForward = useCallback(() => {
    if (!currentStep || isSubmitting || actionLockRef.current) return;

    const currentError = validateStepResponse(currentStep, currentAnswer);
    if (currentError) {
      setValidationMessage(currentError);
      return;
    }

    if (!isLast) {
      actionLockRef.current = true;
      playClick();
      setDirection('exit');
      window.setTimeout(() => {
        setCurrentIndex((previous) => previous + 1);
        setDirection('enter');
        window.setTimeout(() => {
          setDirection('active');
          actionLockRef.current = false;
        }, 50);
      }, 180);
      return;
    }

    const allError = validateAllResponses(form, answers);
    if (allError) {
      setCurrentIndex(allError.index);
      setValidationMessage(allError.message);
      return;
    }

    try {
      actionLockRef.current = true;
      const payload = buildScoreSubmission(form, answers);
      playSuccess();
      setSubmissionPayload(payload);
      setIsSubmitting(true);
    } catch (error) {
      actionLockRef.current = false;
      setValidationMessage(error.message || 'Please review the issued answers.');
    }
  }, [answers, currentAnswer, currentStep, form, isLast, isSubmitting, playClick, playSuccess]);

  const goBackward = useCallback(() => {
    if (isFirst || isSubmitting || actionLockRef.current) return;
    actionLockRef.current = true;
    playClick();
    setDirection('exit');
    window.setTimeout(() => {
      setCurrentIndex((previous) => previous - 1);
      setDirection('enter');
      window.setTimeout(() => {
        setDirection('active');
        actionLockRef.current = false;
      }, 50);
    }, 180);
  }, [isFirst, isSubmitting, playClick]);

  const handleReset = () => {
    playClick();
    setResetModalOpen(true);
  };

  const confirmReset = () => {
    actionLockRef.current = false;
    playClick();
    setAnswers({});
    setCurrentIndex(0);
    setValidationMessage('');
    setDirection('active');
    setResetModalOpen(false);
  };

  const handleExit = () => {
    playClick();
    setExitModalOpen(true);
  };

  const confirmExit = () => {
    playClick();
    setExitModalOpen(false);
    transitionTo('/');
  };

  const handleScoreResult = (scoreData) => {
    const detailedResult = isV2ScoreResponse(scoreData) ? toV2DetailedResult(scoreData) : null;
    const behaviorProfile = detailedResult
      ? buildBehaviorProfileDisplay(form, scoreData)
      : null;
    if (!detailedResult || !behaviorProfile || !saveSignedResult(detailedResult)) {
      actionLockRef.current = false;
      setSubmissionPayload(null);
      setIsSubmitting(false);
      setFormStatus('error');
      setFormError('The server response could not be verified for this browser session. Request a fresh assessment form.');
      return;
    }
    transitionTo('/results', { state: { result: detailedResult, behaviorProfile } });
  };

  const handleSubmissionBack = () => {
    actionLockRef.current = false;
    setIsSubmitting(false);
    setSubmissionPayload(null);
  };

  const renderChoiceControls = (item) => (
    <fieldset className="choice-fieldset" aria-invalid={Boolean(validationMessage)} aria-describedby={validationMessage ? 'assessment-validation-message' : 'answer-hint'}>
      <legend className="sr-only">{item.prompt}</legend>
      <div className="options-list" role="radiogroup" aria-label={item.prompt}>
        {item.options.map((option) => {
          const inputId = `${item.presentation_id}-${option.option_id}`;
          const selected = currentAnswer === option.option_id;
          return (
            <label key={option.option_id} htmlFor={inputId} className={`choice-option option-pill ${selected ? 'selected' : ''}`}>
              <input
                id={inputId}
                className="choice-input"
                type="radio"
                name={item.presentation_id}
                value={option.option_id}
                checked={selected}
                onChange={() => handleChoiceAnswer(option.option_id)}
              />
              <span>{option.label}</span>
            </label>
          );
        })}
      </div>
    </fieldset>
  );

  const renderControls = () => {
    if (!currentStep) return null;
    const { item } = currentStep;

    if (currentStep.kind === 'narrative') {
      return (
        <div className="textarea-wrapper">
          <label className="sr-only" htmlFor="narrative-response">{item.prompt}</label>
          <textarea
            id="narrative-response"
            value={currentAnswer ?? ''}
            onChange={(event) => handleStandardAnswer(event.currentTarget.value)}
            className="input-textarea"
            placeholder="Optional: share a short reflection."
            maxLength={item.max_length}
            rows={6}
            aria-describedby={validationMessage ? 'narrative-meta assessment-validation-message' : 'narrative-meta'}
          />
          <div id="narrative-meta" className="textarea-metadata">
            <span>Optional · never scored</span>
            <span>{String(currentAnswer ?? '').length} / {item.max_length} characters</span>
          </div>
        </div>
      );
    }

    if (item.item_type === 'objective') {
      return (
        <div className="number-input-wrapper">
          <label className="sr-only" htmlFor={`answer-${item.presentation_id}`}>{item.prompt}</label>
          <input
            id={`answer-${item.presentation_id}`}
            type="text"
            inputMode="numeric"
            pattern="-?[0-9]*"
            value={currentAnswer ?? ''}
            onChange={(event) => handleStandardAnswer(event.currentTarget.value)}
            className="input-number"
            placeholder="Enter a whole number"
            aria-describedby={currentErrorId}
            aria-invalid={Boolean(validationMessage)}
            autoFocus
          />
        </div>
      );
    }

    return renderChoiceControls(item);
  };

  if (!hasStarted) {
    return (
      <main className="assessment-layout">
        <button type="button" onClick={handleExit} className="assessment-exit-btn">
          <ArrowLeft size={12} aria-hidden="true" />
          <span>Exit</span>
        </button>

        <div className="assessment-container container">
          <div className="assessment-wrapper">
            <div className="consent-card animate-fade-up">
              <div className="consent-icon animate-pulse-glow">
                <ShieldCheck size={32} aria-hidden="true" />
              </div>
              <h1 className="consent-title gradient-text-accent">
                <TextReveal text="Financial Decision Readiness" />
              </h1>
              <div className="consent-text">
                <p style={{ textAlign: 'center', marginBottom: '24px', color: 'var(--text-secondary)' }}>
                  An anonymous educational assessment of financial knowledge and decision judgement. It does not predict repayment, establish creditworthiness, or make a lending decision.
                </p>
                <div className="telemetry-specs">
                  <div className="spec-item"><ShieldCheck size={16} className="spec-icon" aria-hidden="true" /><span>Server-issued numeric, judgement, and decision-simulation items</span></div>
                  <div className="spec-item"><ShieldCheck size={16} className="spec-icon" aria-hidden="true" /><span>Self-reflection and optional narrative are never scored</span></div>
                  <div className="spec-item"><ShieldCheck size={16} className="spec-icon" aria-hidden="true" /><span>No browser, device, identity, or credit-history data is used</span></div>
                </div>
              </div>
              <button type="button" onClick={handleBegin} className="btn btn-primary" style={{ width: '100%' }}>
                <span>Request assessment form</span>
                <ArrowRight size={16} aria-hidden="true" />
              </button>
            </div>
          </div>
        </div>

        <Modal
          isOpen={exitModalOpen}
          title="Exit Assessment?"
          message="This anonymous attempt will not be saved. Are you sure you want to exit?"
          confirmText="Exit"
          cancelText="Stay"
          onConfirm={confirmExit}
          onCancel={() => { playClick(); setExitModalOpen(false); }}
        />
      </main>
    );
  }

  if (formStatus === 'loading' || formStatus === 'error' || !form) {
    const isLoading = formStatus === 'loading';
    return (
      <main className="processing-layout">
        <button type="button" onClick={handleExit} className="assessment-exit-btn">
          <ArrowLeft size={12} aria-hidden="true" />
          <span>Exit</span>
        </button>
        <SignalCanvas />
        <div className="processing-container container">
          <div className="processing-card" role={isLoading ? 'status' : 'alert'} aria-live="polite">
            <div className="processing-header">
              <span className="processing-title">{isLoading ? 'Requesting secure assessment form' : 'Assessment form unavailable'}</span>
            </div>
            <div className="processing-body">
              {isLoading ? (
                <>
                  <p className="processing-copy">The server is issuing a fresh, one-time form. No answer key is sent to this browser.</p>
                  <div className="processing-meter-container" aria-hidden="true"><div className="processing-meter-fill processing-meter-indeterminate" /></div>
                </>
              ) : (
                <>
                  <p className="processing-copy">{formError || 'The assessment form could not be loaded.'}</p>
                  <div className="processing-actions">
                    <button type="button" className="btn btn-primary" onClick={handleFreshAttempt}>Try again</button>
                    <button type="button" className="btn btn-ghost" onClick={handleExit}>Exit</button>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
        <Modal
          isOpen={exitModalOpen}
          title="Exit Assessment?"
          message="This anonymous attempt will not be saved. Are you sure you want to exit?"
          confirmText="Exit"
          cancelText="Stay"
          onConfirm={confirmExit}
          onCancel={() => { playClick(); setExitModalOpen(false); }}
        />
      </main>
    );
  }

  if (isSubmitting && submissionPayload) {
    return (
      <Processing
        form={form}
        submission={submissionPayload}
        onComplete={handleScoreResult}
        onBack={handleSubmissionBack}
        onFreshAttempt={handleFreshAttempt}
      />
    );
  }

  const progressPercent = ((currentIndex + 1) / steps.length) * 100;
  const stepLabel = getStepLabel(currentStep);
  const currentErrorId = validationMessage ? 'assessment-validation-message' : 'answer-hint';

  return (
    <main className="assessment-layout">
      <div
        className="progress-rail"
        style={{ width: `${progressPercent}%` }}
        role="progressbar"
        aria-valuenow={currentIndex + 1}
        aria-valuemin="1"
        aria-valuemax={steps.length}
        aria-label="Assessment progress"
      />

      <button type="button" onClick={handleExit} className="assessment-exit-btn">
        <ArrowLeft size={12} aria-hidden="true" />
        <span>Exit</span>
      </button>

      <div className="assessment-container container">
        <div className="assessment-wrapper">
          <div className="assessment-header" aria-live="polite">
            <span className="section-indicator">{stepLabel}</span>
            <span className="question-counter">Step {currentIndex + 1} of {steps.length}</span>
          </div>

          <section className={`question-card slide-${direction}`} aria-labelledby="assessment-question-heading">
            <h1
              id="assessment-question-heading"
              ref={questionHeadingRef}
              className="question-text"
              tabIndex="-1"
            >
              {currentStep.item.prompt}
            </h1>
            {currentStep.item.item_type === 'branching' && (
              <p className="question-hint">Stage {currentStep.item.stage_index} of 3 · choose one response.</p>
            )}
            {currentStep.kind === 'behavior' && (
              <p className="question-hint">This self-reflection is shown once in your result and does not affect the score. Choose Not applicable if you prefer not to self-report.</p>
            )}

            <div className="answer-control" aria-describedby={currentErrorId}>
              {renderControls()}
            </div>
            <p id="answer-hint" className="question-hint">{currentStep.kind === 'narrative' ? 'Optional response.' : 'A response is required to continue.'}</p>
            {validationMessage && <p id="assessment-validation-message" className="question-hint validation-message" role="alert">{validationMessage}</p>}
          </section>

          <div className="controls-row">
            <div className="controls-group">
              <button type="button" onClick={goBackward} disabled={isFirst} className="btn btn-ghost" style={{ padding: '10px 18px' }}>
                <ArrowLeft size={14} aria-hidden="true" />
                <span>Back</span>
              </button>
              <button type="button" onClick={handleReset} className="btn btn-ghost reset-button" style={{ padding: '10px 18px' }}>
                <RefreshCw size={12} aria-hidden="true" />
                <span>Reset</span>
              </button>
            </div>

            <button type="button" onClick={goForward} className="btn btn-primary" style={{ minWidth: '120px' }} disabled={isSubmitting}>
              <span>{isLast ? 'Submit securely' : 'Continue'}</span>
              <ArrowRight size={14} aria-hidden="true" />
            </button>
          </div>
        </div>
      </div>

      <Modal
        isOpen={resetModalOpen}
        title="Reset Assessment"
        message="Clear the responses in this server-issued form?"
        confirmText="Reset"
        cancelText="Cancel"
        onConfirm={confirmReset}
        onCancel={() => { playClick(); setResetModalOpen(false); }}
      />

      <Modal
        isOpen={exitModalOpen}
        title="Exit Assessment?"
        message="This anonymous attempt will not be saved. Are you sure you want to exit?"
        confirmText="Exit"
        cancelText="Stay"
        onConfirm={confirmExit}
        onCancel={() => { playClick(); setExitModalOpen(false); }}
      />
    </main>
  );
}
