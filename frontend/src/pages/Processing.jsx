import { useEffect, useRef, useState } from 'react';
import { Check, ShieldAlert } from 'lucide-react';
import SignalCanvas from '../components/hero/SignalCanvas';
import { submitV2Assessment } from '../lib/api';
import {
  formatApiError,
  getApiErrorCode,
  isAttemptLifecycleError,
  isCancellationError,
  isTimeoutError,
} from '../utils/apiErrors';
import useSound from '../hooks/useSound';
import './Processing.css';

const PROCESSING_STEPS = [
  'Validating your responses',
  'Applying the readiness rubric',
  'Signing your result',
];

function shouldRequestFreshAttempt(error) {
  const code = getApiErrorCode(error);
  return isAttemptLifecycleError(error)
    || isTimeoutError(error)
    || !error?.response
    || ['internal_error', 'result_not_found'].includes(code);
}

export default function Processing({ form, submission, onComplete, onBack, onFreshAttempt }) {
  const [activeStep, setActiveStep] = useState(() => (
    typeof window !== 'undefined'
      && window.matchMedia('(prefers-reduced-motion: reduce)').matches
      ? PROCESSING_STEPS.length
      : 0
  ));
  const [error, setError] = useState(null);
  const requestRecordRef = useRef(null);
  const { playStep } = useSound();

  useEffect(() => {
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reducedMotion) return undefined;
    if (activeStep >= PROCESSING_STEPS.length) return undefined;

    const timeout = window.setTimeout(() => {
      setActiveStep((previous) => {
        const next = previous + 1;
        playStep();
        return next;
      });
    }, 420);
    return () => window.clearTimeout(timeout);
  }, [activeStep, playStep]);

  useEffect(() => {
    let record = requestRecordRef.current;
    if (!record || record.controller.signal.aborted) {
      record = {
        controller: new AbortController(),
        active: true,
        started: false,
        finished: false,
        abortTimer: null,
        onComplete,
      };
      requestRecordRef.current = record;
    } else {
      record.active = true;
      record.onComplete = onComplete;
      if (record.abortTimer) window.clearTimeout(record.abortTimer);
    }

    if (!record.started) {
      record.started = true;
      const startedAt = Date.now();

      const submit = async () => {
        try {
          const response = await submitV2Assessment(form, submission, {
            signal: record.controller.signal,
          });
          if (!record.active || record.finished) return;
          record.finished = true;
          const minimumDisplayTime = window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 0 : 600;
          const delay = Math.max(minimumDisplayTime - (Date.now() - startedAt), 0);
          window.setTimeout(() => {
            if (record.active) record.onComplete(response.data);
          }, delay);
        } catch (requestError) {
          if (!record.active || isCancellationError(requestError)) return;
          setError(requestError);
        }
      };

      submit();
    }

    return () => {
      record.active = false;
      record.abortTimer = window.setTimeout(() => {
        if (!record.active && !record.finished) record.controller.abort();
      }, 0);
    };
  }, [form, onComplete, submission]);

  const progressPercent = Math.min((activeStep / PROCESSING_STEPS.length) * 100, 100);
  const isWaitingForScore = activeStep >= PROCESSING_STEPS.length;

  if (error) {
    const freshAttempt = shouldRequestFreshAttempt(error);
    return (
      <div className="processing-layout">
        <SignalCanvas />
        <div className="processing-container container">
          <div className="processing-card processing-error-card" role="alert" aria-live="assertive">
            <div className="processing-header processing-error-header">
              <div className="consent-icon" aria-hidden="true"><ShieldAlert size={28} /></div>
              <span className="processing-title">Submission needs attention</span>
            </div>
            <div className="processing-body">
              <p className="processing-copy">{formatApiError(error, 'The signed result could not be prepared.')}</p>
              <div className="processing-actions">
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={freshAttempt ? onFreshAttempt : onBack}
                >
                  {freshAttempt ? 'Get a fresh form' : 'Return to assessment'}
                </button>
                <button type="button" className="btn btn-ghost" onClick={onBack}>Review responses</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="processing-layout">
      <SignalCanvas />
      <div className="processing-container container">
        <div className="processing-card" role="status" aria-live="polite">
          <div className="processing-header">
            <span className="processing-eyebrow">Assessment complete</span>
            <h1 className="processing-title">Preparing your result</h1>
            <div
              className="processing-meter-container"
              role="progressbar"
              aria-valuenow={activeStep}
              aria-valuemin="0"
              aria-valuemax={PROCESSING_STEPS.length}
              aria-label="Submission progress"
            >
              <div className="processing-meter-fill" style={{ width: `${progressPercent}%` }} />
            </div>
          </div>

          <div className="processing-body">
            <div className="steps-list">
              {PROCESSING_STEPS.map((step, index) => {
                const isCompleted = index < activeStep;
                const isActive = index === activeStep;
                return (
                  <div key={step} className={`step-row ${isCompleted ? 'completed' : ''} ${isActive ? 'active' : ''}`}>
                    <span className="step-icon" aria-hidden="true">
                      {isCompleted ? <Check size={10} className="tick-enter" /> : isActive ? <span className="pulse-indicator" /> : '—'}
                    </span>
                    <span className="step-label">{step}</span>
                    {isActive && <span className="step-status scanning">In progress</span>}
                  </div>
                );
              })}
            </div>

            <div className="processing-footer">
              <span className="processing-eta">
                {isWaitingForScore ? 'Finishing securely…' : 'This usually takes a few seconds.'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
