import { useState, useEffect, useRef } from 'react';
import { ArrowLeft, ArrowRight, RefreshCw, ShieldCheck } from 'lucide-react';
import { QUESTIONS, SECTIONS } from '../data/questions';
import Modal from '../components/ui/Modal';
import TextReveal from '../components/animation/TextReveal';
import Processing from './Processing';
import useSound from '../hooks/useSound';
import usePageTransition from '../hooks/usePageTransition';
import './Assessment.css';

const getNow = () => Date.now();

const SCENARIO_FALLBACKS = {
  scenario_s1: { primary: 's1_b', least: 's1_a', first_click_ms: 0, change_count: 0 },
  scenario_s2: { primary: 's2_b', least: 's2_d', first_click_ms: 0, change_count: 0 },
  scenario_s3: { primary: 's3_b', least: 's3_d', first_click_ms: 0, change_count: 0 },
  scenario_s4: { primary: 's4_b', least: 's4_c', first_click_ms: 0, change_count: 0 },
  scenario_s5: { primary: 's5_b', least: 's5_a', first_click_ms: 0, change_count: 0 },
  scenario_s6: { primary: 's6_b', least: 's6_a', first_click_ms: 0, change_count: 0 },
  scenario_s8: { primary: 's8_b', least: 's8_a', first_click_ms: 0, change_count: 0 },
};

const OPEN_RESPONSE_ACTION_TOKENS = new Set([
  'adapted',
  'adjusted',
  'arranged',
  'asked',
  'budgeted',
  'built',
  'calculated',
  'checked',
  'compared',
  'contacted',
  'created',
  'cut',
  'discussed',
  'earned',
  'found',
  'handled',
  'managed',
  'negotiated',
  'paid',
  'planned',
  'prioritized',
  'reduced',
  'repaid',
  'resolved',
  'saved',
  'scheduled',
  'tracked',
  'worked',
]);
const OPEN_RESPONSE_FIRST_PERSON_TOKENS = new Set(['i', 'me', 'my', 'mine', 'myself', 'we', 'our', 'us']);

function getOpenResponseTokens(value) {
  return String(value || '')
    .toLowerCase()
    .match(/[a-zA-Z']+/g) || [];
}

function isOpenResponseMeaningful(value, minWords = 10) {
  const tokens = getOpenResponseTokens(value);
  if (tokens.length < minWords) return false;
  if (!tokens.some((token) => OPEN_RESPONSE_FIRST_PERSON_TOKENS.has(token))) return false;
  if (!tokens.some((token) => OPEN_RESPONSE_ACTION_TOKENS.has(token))) return false;
  return true;
}

function hasUsableAnswer(question, answer) {
  if (answer === undefined || answer === null) {
    return false;
  }

  if (question.type === 'number') {
    const normalized = String(answer).trim();
    return normalized !== '' && Number.isFinite(Number(normalized));
  }

  if (question.type === 'scenario') {
    return Boolean(
      answer.primary
      && answer.primary !== ''
      && answer.least
      && answer.least !== answer.primary
    );
  }

  if (question.type === 'text') {
    return String(answer).trim() !== '';
  }

  return true;
}

export default function Assessment() {
  const { transitionTo } = usePageTransition();
  const { playClick, playSelect, playSuccess } = useSound();

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
  const sessionStartRef = useRef(null);
  const questionStartRef = useRef(null);
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submissionPayload, setSubmissionPayload] = useState(null);
  const [resetModalOpen, setResetModalOpen] = useState(false);
  const [exitModalOpen, setExitModalOpen] = useState(false);

  // Initialize session times when consented
  useEffect(() => {
    if (consented) {
      if (sessionStartRef.current === null) {
        sessionStartRef.current = getNow();
      }
      if (questionStartRef.current === null) {
        questionStartRef.current = getNow();
      }
    }
  }, [consented]);

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
      questionStartRef.current = getNow();
    }
  }, [currentIndex, consented]);

  const currentQ = QUESTIONS[currentIndex];
  const currentSection = SECTIONS.find((s) => s.id === currentQ.section);
  const isFirst = currentIndex === 0;
  const isLast = currentIndex === QUESTIONS.length - 1;

  // Handle Consent
  const handleConsent = () => {
    playClick();
    sessionStorage.setItem('alterscore_telemetry_consented', 'true');
    setConsented(true);
    sessionStartRef.current = getNow();
    questionStartRef.current = getNow();
  };

  // Record Standard Answer (number, mcq, likert)
  const recordStandardAnswer = (value) => {
    const qId = currentQ.id;
    const now = getNow();
    const rt = now - (questionStartRef.current || now);
    const nextValue = currentQ.type === 'text'
      ? String(value).slice(0, currentQ.maxLength || 1000)
      : value;
    const normalizedNumber =
      currentQ.type === 'number' ? String(nextValue).trim() : null;

    // Track first click
    if (firstClicks[qId] === undefined) {
      setFirstClicks((f) => ({ ...f, [qId]: rt }));
    }

    if (currentQ.type === 'number' && normalizedNumber === '') {
      setAnswers((a) => {
        const rest = { ...a };
        delete rest[qId];
        return rest;
      });
      setResponseTimes((r) => {
        const rest = { ...r };
        delete rest[qId];
        return rest;
      });
      return;
    }

    // Freeform inputs emit on every keystroke, so only discrete choices count as revisions.
    const tracksDiscreteChanges = currentQ.type === 'mcq' || currentQ.type === 'likert';
    const hasExisting = answers[qId] !== undefined;
    if (tracksDiscreteChanges && hasExisting && answers[qId] !== nextValue) {
      setChangeCounts((c) => ({ ...c, [qId]: (c[qId] || 0) + 1 }));
    }

    setAnswers((a) => ({ ...a, [qId]: nextValue }));
    setResponseTimes((r) => ({ ...r, [qId]: rt }));
  };

  // Record Rich Scenario Answer
  const recordScenarioAnswer = (type, optionId) => {
    const qId = currentQ.id;
    const now = getNow();
    const rt = now - (questionStartRef.current || now);

    // Track first click
    if (firstClicks[qId] === undefined) {
      setFirstClicks((f) => ({ ...f, [qId]: rt }));
    }

    setAnswers((prevAnswers) => {
      const prev = prevAnswers[qId] || { primary: '', least: '', first_click_ms: null, change_count: 0 };
      let updated = { ...prev };
      let changeDelta = 0;

      if (type === 'primary') {
        if (updated.primary !== optionId) {
          if (updated.primary) changeDelta += 1;
          if (updated.least === optionId) updated.least = '';
          updated.primary = optionId;
        }
      } else if (type === 'least') {
        if (updated.least !== optionId) {
          if (updated.least) changeDelta += 1;
          if (updated.primary === optionId) updated.primary = '';
          updated.least = optionId;
        }
      }

      updated.change_count = (prev.change_count || 0) + changeDelta;

      if (updated.first_click_ms === null) {
        updated.first_click_ms = rt;
      }

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
      playSuccess();
      submitAssessment();
    } else {
      playClick();
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
      playClick();
      setDirection('exit');
      setTimeout(() => {
        setCurrentIndex((prev) => prev - 1);
        setDirection('enter');
        setTimeout(() => setDirection('active'), 50);
      }, 250);
    }
  };

  const handleStartOver = () => {
    playClick();
    setResetModalOpen(true);
  };

  const confirmReset = () => {
    playClick();
    setAnswers({});
    setCurrentIndex(0);
    setChangeCounts({});
    setFirstClicks({});
    setResponseTimes({});
    setScrollCount(0);
    setDropouts(0);
    sessionStartRef.current = getNow();
    questionStartRef.current = getNow();
    setResetModalOpen(false);
  };

  const handleExit = () => {
    playClick();
    setExitModalOpen(true);
  };

  const confirmExit = () => {
    playClick();
    sessionStorage.removeItem('alterscore_telemetry_consented');
    setConsented(false);
    transitionTo('/');
  };

  // Compile and Submit Telemetry Payload
  const submitAssessment = async () => {
    setIsSubmitting(true);

    const sessionDuration = (getNow() - (sessionStartRef.current || getNow())) / 1000;
    
    // Calculate Average response time
    const rTimes = Object.values(responseTimes);
    const avgRt = rTimes.length > 0 ? rTimes.reduce((a, b) => a + b, 0) / QUESTIONS.length : 4000;

    // Calculate answer change rate
    const changeList = Object.values(changeCounts);
    const totalChanges = changeList.reduce((sum, value) => sum + Math.max(Number(value) || 0, 0), 0);
    const changeRate = Math.min(totalChanges / QUESTIONS.length, 1);

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
    let timeOfDay;
    if (hour >= 5 && hour < 12) timeOfDay = 'morning';
    else if (hour >= 12 && hour < 17) timeOfDay = 'afternoon';
    else if (hour >= 17 && hour < 21) timeOfDay = 'evening';
    else timeOfDay = 'night';

    // Build complete backend payload
    const payload = {
      session_id: crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).substring(2, 15),
      answers: {
        ...answers,
        scenario_s1: answers['scenario_s1'] || SCENARIO_FALLBACKS.scenario_s1,
        scenario_s2: answers['scenario_s2'] || SCENARIO_FALLBACKS.scenario_s2,
        scenario_s3: answers['scenario_s3'] || SCENARIO_FALLBACKS.scenario_s3,
        scenario_s4: answers['scenario_s4'] || SCENARIO_FALLBACKS.scenario_s4,
        scenario_s5: answers['scenario_s5'] || SCENARIO_FALLBACKS.scenario_s5,
        scenario_s6: answers['scenario_s6'] || SCENARIO_FALLBACKS.scenario_s6,
        scenario_s8: answers['scenario_s8'] || SCENARIO_FALLBACKS.scenario_s8,
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
    transitionTo('/results', { state: scoreData });
  };

  const currentAnswer = answers[currentQ.id];
  const hasAnswer = hasUsableAnswer(currentQ, currentAnswer);

  const wordCount = currentQ.type === 'text'
    ? (currentAnswer || '').trim().split(/\s+/).filter(Boolean).length
    : 0;
  const isTextResponseValid = currentQ.type === 'text'
    ? isOpenResponseMeaningful(currentAnswer, currentQ.minWords || 10)
    : true;
  const canContinue = hasAnswer && isTextResponseValid;

  const renderControls = () => {
    if (currentQ.type === 'number') {
      return (
        <div className="number-input-wrapper">
          {currentQ.prefix && <span className="number-prefix">{currentQ.prefix}</span>}
          <input
            type="number"
            inputMode="decimal"
            value={currentAnswer ?? ''}
            onInput={(e) => recordStandardAnswer(e.currentTarget.value)}
            onChange={(e) => recordStandardAnswer(e.currentTarget.value)}
            className="input-number"
            placeholder="0"
            aria-label={currentQ.question}
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
              onClick={() => { recordStandardAnswer(idx); playSelect(); }}
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
                onClick={() => { recordStandardAnswer(val); playSelect(); }}
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
      const scenarioDetails = answers[currentQ.id] || { primary: '', least: '' };
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
                <div>{opt.text}</div>
                <div>
                  <button
                    onClick={() => { recordScenarioAnswer('primary', opt.id); playSelect(); }}
                    className={`badge-tag ${isPrimary ? 'primary' : 'option-pill-btn'}`}
                    style={{ border: 'none', cursor: 'pointer' }}
                  >
                    Most
                  </button>
                  <button
                    onClick={() => { recordScenarioAnswer('least', opt.id); playSelect(); }}
                    className={`badge-tag ${isLeast ? 'least' : 'option-pill-btn'}`}
                    style={{ border: 'none', cursor: 'pointer' }}
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
            value={currentAnswer ?? ''}
            onChange={(e) => recordStandardAnswer(e.target.value)}
            className="input-textarea"
            placeholder="Type your response..."
            aria-label={currentQ.question}
            maxLength={currentQ.maxLength || 1000}
            rows={5}
          />
          <div className="textarea-metadata">
            <span className={`word-count-status ${isTextResponseValid ? 'valid' : 'invalid'}`}>
              {wordCount} words {isTextResponseValid ? 'OK: includes your action' : `(Use at least ${minWords} words, first-person language, and a concrete action)`}
            </span>
            <span>Max {currentQ.maxLength || 1000} chars</span>
          </div>
          <div className="textarea-progress-bar">
            <div
              className="textarea-progress-fill"
              style={{
                width: `${progressPercent}%`,
                backgroundColor: isTextResponseValid ? 'var(--accent-emerald)' : 'var(--accent-rose)',
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
        <button onClick={handleExit} className="assessment-exit-btn">
          <ArrowLeft size={12} />
          <span>Exit</span>
        </button>

        <div className="assessment-container container">
          <div className="assessment-wrapper">
            <div className="consent-card animate-fade-up">
              <div className="consent-icon animate-pulse-glow">
                <ShieldCheck size={32} />
              </div>
              <h2 className="consent-title gradient-text-accent">
                <TextReveal text="Signal Authorization" />
              </h2>
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

        <Modal
          isOpen={exitModalOpen}
          title="Exit Assessment?"
          message="Your psychometric answers and telemetry session data will be discarded. Are you sure you want to exit?"
          confirmText="Exit"
          cancelText="Stay"
          onConfirm={confirmExit}
          onCancel={() => { playClick(); setExitModalOpen(false); }}
        />
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

      <button onClick={handleExit} className="assessment-exit-btn">
        <ArrowLeft size={12} />
        <span>Exit</span>
      </button>

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
        onCancel={() => { playClick(); setResetModalOpen(false); }}
      />

      {/* Custom Modal for Exit Confirmation */}
      <Modal
        isOpen={exitModalOpen}
        title="Exit Assessment?"
        message="Your psychometric answers and telemetry session data will be discarded. Are you sure you want to exit?"
        confirmText="Exit"
        cancelText="Stay"
        onConfirm={confirmExit}
        onCancel={() => { playClick(); setExitModalOpen(false); }}
      />
    </div>
  );
}
