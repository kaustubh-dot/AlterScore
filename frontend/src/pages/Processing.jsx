import { useEffect, useState, useRef } from 'react';
import { ShieldAlert, Check } from 'lucide-react';
import SignalCanvas from '../components/hero/SignalCanvas';
import useSound from '../hooks/useSound';
import api from '../lib/api';
import { formatApiError } from '../utils/apiErrors';
import './Processing.css';
export default function Processing({ payload, onComplete }) {
  const [activeStep, setActiveStep] = useState(0);
  const [error, setError] = useState(null);
  const requestFiredRef = useRef(false);
  const { playStep } = useSound();

  const steps = [
    { label: 'Parsing psychometric responses' },
    { label: 'Extracting behavioral telemetry' },
    { label: 'Running NLP semantic scanner' },
    { label: 'Computing derived features' },
    { label: 'Applying governance constraints' },
    { label: 'Calibrating score bands' },
  ];

  // Steps transition effect
  useEffect(() => {
    if (activeStep >= steps.length) return;
    const interval = setTimeout(() => {
      setActiveStep((prev) => {
        const next = prev + 1;
        playStep();
        return next;
      });
    }, 600);
    return () => clearTimeout(interval);
  }, [activeStep, playStep, steps.length]);

  // Firing API request to score
  useEffect(() => {
    if (requestFiredRef.current) return;
    requestFiredRef.current = true;

    const startTime = Date.now();

    const computeScore = async () => {
      try {
        const response = await api.post('/score', payload);
        const delay = Math.max(3600 - (Date.now() - startTime), 500);
        setTimeout(() => {
          onComplete(response.data);
        }, delay);
      } catch (err) {
        if (import.meta.env.DEV) {
          console.warn('Score request failed:', {
            status: err?.response?.status,
            code: err?.code,
            message: err?.message,
          });
        }
        setError(formatApiError(err, 'Internal server issue.'));
      }
    };

    computeScore();
  }, [payload, onComplete]);

  const progressPercent = Math.min((activeStep / steps.length) * 100, 100);

  if (error) {
    return (
      <div className="processing-layout">
        <SignalCanvas />
        <div className="processing-container container">
          <div className="processing-card" style={{ borderColor: 'rgba(244, 63, 94, 0.3)' }}>
            <div className="processing-header" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px' }}>
              <div className="consent-icon animate-pulse-glow" style={{ borderColor: 'rgba(244, 63, 94, 0.4)', color: 'var(--accent-rose)' }}>
                <ShieldAlert size={28} />
              </div>
              <span className="processing-title" style={{ color: 'var(--accent-rose)', letterSpacing: '0.08em' }}>Submission Rejected</span>
            </div>
            
            <div className="processing-body" style={{ padding: 'var(--space-6) 0', textAlign: 'center' }}>
              <p style={{ color: 'var(--text-secondary)', fontSize: '13px', lineHeight: 1.6, marginBottom: '24px', maxWidth: '480px', marginLeft: 'auto', marginRight: 'auto' }}>
                {error}
              </p>
              
              <button 
                onClick={() => window.location.reload()} 
                className="btn btn-primary"
                style={{ 
                  margin: '0 auto', 
                  borderColor: 'rgba(244, 63, 94, 0.3)', 
                  background: 'rgba(244, 63, 94, 0.1)',
                  color: '#FFFFFF' 
                }}
              >
                <span>Go Back & Restart</span>
              </button>
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
        <div className="processing-card">
          <div className="processing-header">
            <span className="processing-title">Cognitive Pipeline Calibration</span>
            <div className="processing-meter-container">
              <div 
                className="processing-meter-fill"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          </div>
          
          <div className="processing-body">
            <div className="steps-list">
              {steps.map((step, idx) => {
                const isCompleted = idx < activeStep;
                const isActive = idx === activeStep;
                
                return (
                  <div 
                    key={idx} 
                    className={`step-row ${isCompleted ? 'completed' : ''} ${isActive ? 'active' : ''}`}
                  >
                    <span className="step-icon">
                      {isCompleted ? (
                        <Check size={10} className="tick-enter" />
                      ) : isActive ? (
                        <span className="pulse-indicator" />
                      ) : (
                        '—'
                      )}
                    </span>
                    <span className="step-label">{step.label}</span>
                    {isCompleted && <span className="step-status">COMPLETED</span>}
                    {isActive && <span className="step-status scanning">PROCESSING</span>}
                  </div>
                );
              })}
            </div>
            
            <div className="processing-footer">
              <span className="processing-eta">
                Calibrating behavioral telemetry • Please wait
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
