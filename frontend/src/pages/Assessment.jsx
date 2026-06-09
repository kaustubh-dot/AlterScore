import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { ArrowLeft, ArrowRight, RefreshCw, Terminal, Eye, ShieldCheck } from 'lucide-react';
import { QUESTIONS, SECTIONS } from '../data/questions';
import Modal from '../components/ui/Modal';
import './Assessment.css';
import Processing from './Processing';

export default function Assessment() {
  const navigate = useNavigate();

  // Telemetry Consent
  const [consented, setConsented] = useState(() => {
    return sessionStorage.getItem('alterscore_telemetry_consented') === 'true';
  });

  // Assessment Progress State
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [direction, setDirection] = useState('active'); // active, enter, exit

  // Telemetry Logs State
  const [changeCounts, setChangeCounts] = useState({});
  const [firstClicks, setFirstClicks] = useState({});
  const [responseTimes, setResponseTimes] = useState({});
  const [scrollCount, setScrollCount] = useState(0);
  const [dropouts, setDropouts] = useState(0);

  // Time & Session Markers
  const sessionStartRef = useRef(Date.now());
  const questionStartRef = useRef(Date.now());
  
  // HUD toggling
  const [hudOpen, setHudOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submissionPayload, setSubmissionPayload] = useState(null);
  const [resetModalOpen, setResetModalOpen] = useState(false);

  // Track scroll hesitation
  useEffect(() => {
    if (!consented) return;
    const handleScroll = () => {
      setScrollCount((s) => s + 1);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    window.addEventListener('wheel', handleScroll, { passive: true });

    // Track tab dropout count (blur events)
    const handleBlur = () => {
      setDropouts((d) => d + 1);
    };
    window.addEventListener('blur', handleBlur);

    return () => {
      window.removeEventListener('scroll', handleScroll);
      window.removeEventListener('wheel', handleScroll);
      window.removeEventListener('blur', handleBlur);
    };
  }, [consented]);

  // Track question start times
  useEffect(() => {
    if (consented) {
      questionStartRef.current = Date.now();
    }
  }, [currentIndex, consented]);

  const currentQ = QUESTIONS[currentIndex];
  const currentSection = SECTIONS.find((s) => s.id === currentQ.section);
  const isFirst = currentIndex === 0;
  const isLast = currentIndex === QUESTIONS.length - 1;

  // Handle Consent
  const handleConsent = () => {
    sessionStorage.setItem('alterscore_telemetry_consented', 'true');
    setConsented(true);
    sessionStartRef.current = Date.now();
    questionStartRef.current = Date.now();
  };

  // Record Standard Answer (number, mcq, likert)
  const recordStandardAnswer = (value) => {
    const qId = currentQ.id;
    const now = Date.now();
    const rt = now - questionStartRef.current;

    // Track first click
    if (firstClicks[qId] === undefined) {
      setFirstClicks((f) => ({ ...f, [qId]: rt }));
    }

    // Track change count
    const hasExisting = answers[qId] !== undefined;
    if (hasExisting && answers[qId] !== value) {
      setChangeCounts((c) => ({ ...c, [qId]: (c[qId] || 0) + 1 }));
    }

    setAnswers((a) => ({ ...a, [qId]: value }));
    setResponseTimes((r) => ({ ...r, [qId]: rt }));
  };

  // Record Rich Scenario Answer
  const recordScenarioAnswer = (type, optionId) => {
    const qId = currentQ.id;
    const now = Date.now();
    const rt = now - questionStartRef.current;

    // Track first click
    if (firstClicks[qId] === undefined) {
      setFirstClicks((f) => ({ ...f, [qId]: rt }));
    }

    setAnswers((prevAnswers) => {
      const prev = prevAnswers[qId] || { primary: '', least: null, first_click_ms: null, change_count: 0 };
      let updated = { ...prev };

      if (type === 'primary') {
        // If they click primary on something already selected as least, clear least
        if (updated.least === optionId) updated.least = null;
        if (updated.primary !== optionId) {
          updated.change_count += 1;
          updated.primary = optionId;
        }
      } else if (type === 'least') {
        // If they click least on something already selected as primary, clear primary
        if (updated.primary === optionId) updated.primary = '';
        if (updated.least !== optionId) {
          updated.change_count += 1;
          updated.least = optionId;
        }
      }

      // Record first click ms inside the object
      if (updated.first_click_ms === null) {
        updated.first_click_ms = rt;
      }

      // Save change count telemetry
      setChangeCounts((c) => ({ ...c, [qId]: updated.change_count }));

      return {
        ...prevAnswers,
        [qId]: updated,
      };
    });

    setResponseTimes((r) => ({ ...r, [qId]: rt }));
  };

  // Slide Transitions & Next
  const goForward = () => {
    if (isLast) {
      submitAssessment();
    } else {
      setDirection('exit');
      setTimeout(() => {
        setCurrentIndex((prev) => prev + 1);
        setDirection('enter');
        setTimeout(() => setDirection('active'), 50);
      }, 250);
    }
  };

  const goBackward = () => {
    if (!isFirst) {
      setDirection('exit');
      setTimeout(() => {
        setCurrentIndex((prev) => prev - 1);
        setDirection('enter');
        setTimeout(() => setDirection('active'), 50);
      }, 250);
    }
  };

  const handleStartOver = () => {
    setResetModalOpen(true);
  };

  const confirmReset = () => {
    setAnswers({});
    setCurrentIndex(0);
    setChangeCounts({});
    setFirstClicks({});
    setResponseTimes({});
    setScrollCount(0);
    setDropouts(0);
    sessionStartRef.current = Date.now();
    questionStartRef.current = Date.now();
    setResetModalOpen(false);
  };

  // Compile and Submit Telemetry Payload
  const submitAssessment = async () => {
    setIsSubmitting(true);

    const sessionDuration = (Date.now() - sessionStartRef.current) / 1000;
    
    // Calculate Average response time
    const rTimes = Object.values(responseTimes);
    const avgRt = rTimes.length > 0 ? rTimes.reduce((a, b) => a + b, 0) / QUESTIONS.length : 4000;

    // Calculate answer change rate
    const changeList = Object.values(changeCounts);
    const totalChanges = changeList.filter((v) => v > 0).length;
    const changeRate = totalChanges / QUESTIONS.length;

    // Calculate typing speed on open response text
    const openText = answers['open_response_text'] || '';
    const openTextTimeMs = responseTimes['open_response_text'] || 5000;
    const characterCount = openText.length;
    const typingSpeedWpm = openTextTimeMs > 1000 
      ? Math.min(((characterCount / 5) / (openTextTimeMs / 60000)), 200.0)
      : 0.0;

    // Calculate risk response speed ratio
    const riskQuestions = ['scenario_s1', 'scenario_s4'];
    const riskRts = riskQuestions.map(id => responseTimes[id]).filter(Boolean);
    const nonRiskRts = QUESTIONS.filter(q => !riskQuestions.includes(q.id))
      .map(q => responseTimes[q.id])
      .filter(Boolean);

    const avgRiskRt = riskRts.length > 0 ? riskRts.reduce((a,b)=>a+b,0) / riskRts.length : 4000;
    const avgNonRiskRt = nonRiskRts.length > 0 ? nonRiskRts.reduce((a,b)=>a+b,0) / nonRiskRts.length : 4000;
    const riskRatio = Math.min(Math.max(avgRiskRt / avgNonRiskRt, 0.1), 5.0);

    // Detect device type
    const ua = navigator.userAgent;
    let deviceType = 'desktop';
    if (/tablet|ipad|playbook|silk/i.test(ua)) {
      deviceType = 'tablet';
    } else if (/mobile|iphone|ipod|android|blackberry|opera mini|iemobile/i.test(ua)) {
      deviceType = 'mobile';
    }

    // Detect time of day
    const hour = new Date().getHours();
    let timeOfDay = 'afternoon';
    if (hour >= 5 && hour < 12) timeOfDay = 'morning';
    else if (hour >= 12 && hour < 17) timeOfDay = 'afternoon';
    else if (hour >= 17 && hour < 21) timeOfDay = 'evening';
    else timeOfDay = 'night';

    // Build complete backend payload
    const payload = {
      session_id: crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).substring(2, 15),
      answers: {
        ...answers,
        scenario_s1: answers['scenario_s1'] || { primary: 's1_b', least: null, first_click_ms: 0, change_count: 0 },
        scenario_s2: answers['scenario_s2'] || { primary: 's2_b', least: null, first_click_ms: 0, change_count: 0 },
        scenario_s3: answers['scenario_s3'] || { primary: 's3_b', least: null, first_click_ms: 0, change_count: 0 },
        scenario_s4: answers['scenario_s4'] || { primary: 's4_b', least: null, first_click_ms: 0, change_count: 0 },
        scenario_s5: answers['scenario_s5'] || { primary: 's5_b', least: null, first_click_ms: 0, change_count: 0 },
        scenario_s6: answers['scenario_s6'] || { primary: 's6_b', least: null, first_click_ms: 0, change_count: 0 },
        scenario_s8: answers['scenario_s8'] || { primary: 's8_b', least: null, first_click_ms: 0, change_count: 0 },
        honesty_trap_q1: answers['honesty_trap_q1'] !== undefined ? Number(answers['honesty_trap_q1']) : 3,
        open_response_text: answers['open_response_text'] || '',
      },
      behavioral: {
        avg_response_time_ms: avgRt,
        answer_change_rate: changeRate,
        session_duration_sec: sessionDuration,
        dropout_count: Math.min(dropouts, 20),
        scroll_hesitation_score: Math.min(scrollCount / 40.0, 1.0),
        risk_response_speed_ratio: riskRatio,
        typing_speed_wpm: typingSpeedWpm,
        device_type: deviceType,
        time_of_day: timeOfDay,
      },
    };

    setSubmissionPayload(payload);
  };

  const handleScoreResult = (scoreData) => {
    navigate('/results', { state: scoreData });
  };

  const currentAnswer = answers[currentQ.id];
  const hasAnswer = currentAnswer !== undefined && (
    currentQ.type !== 'scenario' || (currentAnswer.primary && currentAnswer.primary !== '')
  );

  const wordCount = currentQ.type === 'text' 
    ? (currentAnswer || '').trim().split(/\s+/).filter(Boolean).length 
    : 0;
  const isWordCountValid = currentQ.type === 'text' ? wordCount >= (currentQ.minWords || 10) : true;
  const canContinue = hasAnswer && isWordCountValid;

  const renderControls = () => {
    if (currentQ.type === 'number') {
      return (
        <div className="number-input-wrapper">
          {currentQ.prefix && <span className="number-prefix">{currentQ.prefix}</span>}
          <input
            type="number"
            value={currentAnswer || ''}
            onChange={(e) => recordStandardAnswer(e.target.value)}
            className="input-number"
            placeholder="0"
            autoFocus
          />
          {currentQ.suffix && <span className="number-suffix">{currentQ.suffix}</span>}
        </div>
      );
    }

    if (currentQ.type === 'mcq') {
      return (
        <div className="options-list">
          {currentQ.options.map((opt, idx) => (
            <button
              key={idx}
              onClick={() => recordStandardAnswer(idx)}
              className={`option-pill ${currentAnswer === idx ? 'selected' : ''}`}
            >
              {opt}
            </button>
          ))}
        </div>
      );
    }

    if (currentQ.type === 'likert') {
      return (
        <div className="likert-scale">
          {currentQ.scale.map((label, idx) => {
            const val = idx + 1;
            return (
              <button
                key={idx}
                onClick={() => recordStandardAnswer(val)}
                className={`likert-option ${currentAnswer === val ? 'selected' : ''}`}
              >
                <span className="likert-number">{val}</span>
                <span className="likert-label">{label}</span>
              </button>
            );
          })}
        </div>
      );
    }

    if (currentQ.type === 'scenario') {
      const scenarioDetails = answers[currentQ.id] || { primary: '', least: null };
      return (
        <div className="options-list">
          {currentQ.options.map((opt, idx) => {
            const isPrimary = scenarioDetails.primary === opt.id;
            const isLeast = scenarioDetails.least === opt.id;
            return (
              <div
                key={idx}
                className={`scenario-pill ${isPrimary ? 'primary-selected' : ''} ${isLeast ? 'least-selected' : ''}`}
              >
                <div style={{ flex: 1, paddingRight: '12px' }}>{opt.text}</div>
                <div style={{ display: 'flex', gap: '6px' }}>
                  <button
                    onClick={() => recordScenarioAnswer('primary', opt.id)}
                    className={`badge-tag ${isPrimary ? 'primary' : 'option-pill-btn'}`}
                    style={{ border: 'none', cursor: 'pointer', padding: '4px 8px', fontSize: '9px' }}
                  >
                    Most
                  </button>
                  <button
                    onClick={() => recordScenarioAnswer('least', opt.id)}
                    className={`badge-tag ${isLeast ? 'least' : 'option-pill-btn'}`}
                    style={{ border: 'none', cursor: 'pointer', padding: '4px 8px', fontSize: '9px' }}
                  >
                    Least
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      );
    }

    if (currentQ.type === 'text') {
      const minWords = currentQ.minWords || 10;
      const progressPercent = Math.min((wordCount / minWords) * 100, 100);

      return (
        <div className="textarea-wrapper">
          <textarea
            value={currentAnswer || ''}
            onChange={(e) => recordStandardAnswer(e.target.value)}
            className="input-textarea"
            placeholder="Type your response..."
            rows={5}
          />
          <div className="textarea-metadata">
            <span className={`word-count-status ${isWordCountValid ? 'valid' : 'invalid'}`}>
              {wordCount} words {isWordCountValid ? '✓ Met' : `(Need at least ${minWords})`}
            </span>
            <span>Max {currentQ.maxLength || 1000} chars</span>
          </div>
          <div className="textarea-progress-bar">
            <div
              className="textarea-progress-fill"
              style={{
                width: `${progressPercent}%`,
                backgroundColor: isWordCountValid ? 'var(--accent-emerald)' : 'var(--accent-rose)',
              }}
            />
          </div>
        </div>
      );
    }

    return null;
  };

  if (!consented) {
    return (
      <div className="assessment-layout">
        <div className="assessment-container container">
          <div className="assessment-wrapper">
            <div className="consent-card animate-fade-up">
              <div className="consent-icon animate-pulse-glow">
                <Terminal size={32} />
              </div>
              <h2 className="consent-title gradient-text-accent">Signal Authorization</h2>
              <div className="consent-text">
                <p style={{ textAlign: 'center', marginBottom: '24px', color: 'var(--text-secondary)' }}>
                  We measure analytical reasoning and behavioral telemetry, not transactions.
                </p>
                <div className="telemetry-specs">
                  <div className="spec-item">
                    <ShieldCheck size={16} className="spec-icon" />
                    <span>Response latency and hesitation patterns</span>
                  </div>
                  <div className="spec-item">
                    <ShieldCheck size={16} className="spec-icon" />
                    <span>Answer change rates and typing dynamics</span>
                  </div>
                  <div className="spec-item">
                    <ShieldCheck size={16} className="spec-icon" />
                    <span>Secure, locally-computed psychometric profiling</span>
                  </div>
                </div>
              </div>
              <button onClick={handleConsent} className="btn btn-primary" style={{ width: '100%' }}>
                <span>Authorize & Begin</span>
                <ArrowRight size={16} />
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (isSubmitting && submissionPayload) {
    return (
      <Processing 
        payload={submissionPayload} 
        onComplete={handleScoreResult} 
      />
    );
  }

  const progressPercent = ((currentIndex + 1) / QUESTIONS.length) * 100;

  return (
    <div className="assessment-layout">
      {/* Top Progress Rail */}
      <div className="progress-rail" style={{ width: `${progressPercent}%` }} />

      <div className="assessment-container container">
        <div className="assessment-wrapper">
          {/* Header metadata */}
          <div className="assessment-header">
            <span className="section-indicator">
              {currentSection ? `Section ${currentSection.id} — ${currentSection.title}` : ''}
            </span>
            <span className="question-counter">
              Question {currentIndex + 1} / {QUESTIONS.length}
            </span>
          </div>

          {/* Question Card */}
          <div className={`question-card slide-${direction}`}>
            <p className="question-text">{currentQ.question}</p>
            {currentQ.hint && <p className="question-hint">{currentQ.hint}</p>}
            
            <div className="answer-control">
              {renderControls()}
            </div>
          </div>

          {/* Nav Controls */}
          <div className="controls-row">
            <div className="controls-group">
              <button
                onClick={goBackward}
                disabled={isFirst}
                className="btn btn-ghost"
                style={{ padding: '10px 18px' }}
              >
                <ArrowLeft size={14} />
                <span>Back</span>
              </button>
              
              <button
                onClick={handleStartOver}
                className="btn btn-ghost"
                style={{ padding: '10px 18px', borderColor: 'rgba(244, 63, 94, 0.15)', color: 'var(--accent-rose)' }}
              >
                <RefreshCw size={12} />
                <span>Reset</span>
              </button>
            </div>

            <button
              onClick={goForward}
              disabled={!canContinue}
              className={`btn ${canContinue ? 'btn-primary' : 'btn-ghost'}`}
              style={{ minWidth: '120px' }}
            >
              <span>{isLast ? 'Submit' : 'Continue'}</span>
              <ArrowRight size={14} />
            </button>
          </div>
        </div>
      </div>

      {/* Custom Modal for Reset Confirmation */}
      <Modal
        isOpen={resetModalOpen}
        title="Reset Assessment"
        message="Are you sure you want to clear your current progress and reset telemetry logs?"
        confirmText="Reset"
        cancelText="Cancel"
        onConfirm={confirmReset}
        onCancel={() => setResetModalOpen(false)}
      />

      {/* Interactive Telemetry Diagnostics HUD */}
      <div className="diagnostics-hud">
        {hudOpen && (
          <div className="hud-window">
            <div className="hud-header">
              <span>sys_telemetry.hud</span>
              <span className="hud-status-dot" />
            </div>
            <div className="hud-grid">
              <div className="hud-row">
                <span className="hud-label">Active Index:</span>
                <span className="hud-value highlight">Q{currentIndex + 1}</span>
              </div>
              <div className="hud-row">
                <span className="hud-label">Current Q ID:</span>
                <span className="hud-value">{currentQ.id}</span>
              </div>
              <div className="hud-row">
                <span className="hud-label">Current RT:</span>
                <span className="hud-value">
                  {Math.round(Date.now() - questionStartRef.current)} ms
                </span>
              </div>
              <div className="hud-row">
                <span className="hud-label">First Click RT:</span>
                <span className="hud-value">
                  {firstClicks[currentQ.id] !== undefined ? `${Math.round(firstClicks[currentQ.id])} ms` : 'N/A'}
                </span>
              </div>
              <div className="hud-row">
                <span className="hud-label">Q Changes:</span>
                <span className="hud-value">{changeCounts[currentQ.id] || 0}</span>
              </div>
              <div className="hud-row">
                <span className="hud-label">Scroll Hesitations:</span>
                <span className="hud-value highlight">{scrollCount}</span>
              </div>
              <div className="hud-row">
                <span className="hud-label">Attention Blurs:</span>
                <span className="hud-value highlight">{dropouts}</span>
              </div>
              <div className="hud-row" style={{ marginTop: '4px', paddingTop: '4px', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                <span className="hud-label">Session Duration:</span>
                <span className="hud-value">
                  {Math.round((Date.now() - sessionStartRef.current) / 1000)}s
                </span>
              </div>
              <div className="hud-row">
                <span className="hud-label">Avg RT Overall:</span>
                <span className="hud-value">
                  {Object.keys(responseTimes).length > 0 
                    ? `${Math.round(Object.values(responseTimes).reduce((a,b)=>a+b,0) / Object.keys(responseTimes).length)} ms` 
                    : 'N/A'}
                </span>
              </div>
              <div className="hud-row">
                <span className="hud-label">Change Rate:</span>
                <span className="hud-value">
                  {(Object.values(changeCounts).filter(c=>c>0).length / QUESTIONS.length).toFixed(3)}
                </span>
              </div>
            </div>
          </div>
        )}
        <button
          onClick={() => setHudOpen(!hudOpen)}
          className={`hud-toggle-btn ${hudOpen ? 'active' : ''}`}
        >
          <Terminal size={12} style={{ marginRight: '6px', display: 'inline', verticalAlign: 'middle' }} />
          {hudOpen ? 'Hide Diagnostics' : 'Diagnostics Console'}
        </button>
      </div>
    </div>
  );
}
