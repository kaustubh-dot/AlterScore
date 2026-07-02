import { useEffect, useRef, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { Sliders, RotateCcw, LayoutDashboard, AlertCircle, Minus, Plus } from 'lucide-react';
import ScrollReveal from '../components/animation/ScrollReveal';
import GlowCard from '../components/ui/GlowCard';
import TextReveal from '../components/animation/TextReveal';
import useSound from '../hooks/useSound';
import usePageTransition from '../hooks/usePageTransition';
import './Results.css';

const SCORE_MIN = 300;
const SCORE_RANGE = 550;

function asArray(value) {
  return Array.isArray(value) ? value : [];
}

function formatBandLabel(band) {
  return String(band || '')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function getBandInfoForScore(score) {
  if (score >= 750) {
    return {
      band: 'excellent',
      color: 'var(--score-excellent)',
      shadow: 'var(--shadow-score-excellent)',
      loanMin: 30000,
      loanMax: 75000,
      description: 'Microloans up to Rs. 75,000 approved. Extremely low default probability.',
    };
  }
  if (score >= 650) {
    return {
      band: 'good',
      color: 'var(--score-good)',
      shadow: 'var(--shadow-score-good)',
      loanMin: 10000,
      loanMax: 30000,
      description: 'Microloans up to Rs. 30,000 approved. Solid repayment probability.',
    };
  }
  if (score >= 550) {
    return {
      band: 'fair',
      color: 'var(--score-fair)',
      shadow: 'var(--shadow-score-fair)',
      loanMin: 5000,
      loanMax: 12000,
      description: 'Microloans up to Rs. 12,000 approved. Moderate risk conditions apply.',
    };
  }
  if (score >= 450) {
    return {
      band: 'poor',
      color: 'var(--score-poor)',
      shadow: 'var(--shadow-score-poor)',
      loanMin: 0,
      loanMax: 5000,
      description: 'Microloans up to Rs. 5,000 approved. Sub-prime risk controls active.',
    };
  }
  return {
    band: 'very_poor',
    color: 'var(--score-very-poor)',
    shadow: 'var(--shadow-score-very-poor)',
    loanMin: 0,
    loanMax: 0,
    description: 'Funding deferred. Score below threshold. Credit counselling recommended.',
  };
}

function getBandColor(band, fallbackScore) {
  const normalizedBand = String(band || '').toLowerCase();
  if (normalizedBand.includes('excellent')) return 'var(--score-excellent)';
  if (normalizedBand.includes('good')) return 'var(--score-good)';
  if (normalizedBand.includes('fair')) return 'var(--score-fair)';
  if (normalizedBand.includes('poor') && !normalizedBand.includes('very')) return 'var(--score-poor)';
  if (normalizedBand.includes('very')) return 'var(--score-very-poor)';
  return getBandInfoForScore(fallbackScore).color;
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

export default function Results() {
  const location = useLocation();
  const { transitionTo } = usePageTransition();
  const { playSuccess, playClick } = useSound();
  const playSuccessRef = useRef(playSuccess);
  
  const [scoreData] = useState(() => {
    if (location.state) return location.state;

    const saved = localStorage.getItem('alterscore_results');
    if (!saved) return null;

    try {
      return JSON.parse(saved);
    } catch {
      return null;
    }
  });
  
  // Persist score to localStorage for borrower dashboard restoration
  useEffect(() => {
    if (scoreData) {
      localStorage.setItem('alterscore_results', JSON.stringify(scoreData));
    }
  }, [scoreData]);

  // Animation Stages
  const [animationStep, setAnimationStep] = useState(0); // 0: void, 1: ring, 2: countup, 3: glow, 4: content
  const [displayScore, setDisplayScore] = useState(300);
  const [ringOffset, setRingOffset] = useState(440); // Circle perimeter for stroke-dashoffset

  useEffect(() => {
    playSuccessRef.current = playSuccess;
  }, [playSuccess]);

  // Derived slider metrics based on user's actual choices
  const [originalVals] = useState(() => {
    if (!scoreData) return null;
    const explanation = asArray(scoreData.explanation);
    const governanceSignals = scoreData.governance_signals || {};
    const isGaming = scoreData.credit_score < 400 && explanation.some(e => e.feature === 'avg_response_time_ms' && e.shap_value < 0);
    const isCRTCorrect = explanation.some(e => e.feature === 'CRT_score' && e.shap_value > 0);
    const consistencySignal = explanation.find(e => e.feature === 'scenario_consistency_score');
    const scenarioConsistency = typeof governanceSignals.scenario_consistency_score === 'number'
      ? governanceSignals.scenario_consistency_score
      : null;
    return {
      pace: isGaming ? 1.5 : 5.0,
      crt: isCRTCorrect ? 2 : 0,
      consistency: scenarioConsistency !== null
        ? (scenarioConsistency >= 0.9 ? 1 : 0)
        : (consistencySignal ? (consistencySignal.shap_value > 0 ? 1 : 0) : 1)
    };
  });

  // Interactive Optimizer Playground State
  const [optPace, setOptPace] = useState(() => originalVals?.pace ?? 5.0); // response pace in seconds
  const [optCRT, setOptCRT] = useState(() => originalVals?.crt ?? 0); // CRT answers correct (0-2)
  const [optConsistency, setOptConsistency] = useState(() => originalVals?.consistency ?? 0); // 0 (mismatch) or 1 (match)
  const [simulatorTouched, setSimulatorTouched] = useState(false);

  // Trigger Cinematic Reveal Animation
  useEffect(() => {
    if (!scoreData) return;

    const target = scoreData.credit_score;
    const targetPercentage = (target - 300) / 550;

    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      const timeout = setTimeout(() => {
        setAnimationStep(4);
        setDisplayScore(target);
        setRingOffset(440 - 440 * targetPercentage);
      }, 0);
      return () => clearTimeout(timeout);
    }

    const t1 = setTimeout(() => {
      setAnimationStep(1);
      setRingOffset(440 - 440 * targetPercentage);
    }, 200);

    const t2 = setTimeout(() => {
      setAnimationStep(2);
      const duration = 1200;
      const startTime = performance.now();

      const step = (timestamp) => {
        const elapsed = timestamp - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const ease = progress * (2 - progress);
        const current = 300 + ease * (target - 300);
        
        setDisplayScore(Math.floor(current));

        if (progress < 1) {
          requestAnimationFrame(step);
        } else {
          setDisplayScore(target);
        }
      };
      requestAnimationFrame(step);
    }, 800);

    const t3 = setTimeout(() => {
      setAnimationStep(3);
      playSuccessRef.current(); // Play cinematic sound chord when glow pops.
    }, 2000);

    const t4 = setTimeout(() => {
      setAnimationStep(4);
    }, 2800);

    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
      clearTimeout(t3);
      clearTimeout(t4);
    };
  }, [scoreData]);

  if (!scoreData) {
    return (
      <div className="results-layout" style={{ justifyContent: 'center', alignItems: 'center' }}>
        <div className="container" style={{ textAlign: 'center', maxWidth: '400px' }}>
          <AlertCircle size={48} style={{ color: 'var(--accent-rose)', marginBottom: '16px' }} />
          <h2 style={{ fontFamily: 'var(--font-display)', marginBottom: '8px' }}>No Profile Found</h2>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '24px', fontSize: '14px' }}>
            Please complete the psychometric assessment to generate your credit intelligence score.
          </p>
          <button onClick={() => transitionTo('/assessment')} className="btn btn-primary" style={{ width: '100%' }}>
            Start Assessment
          </button>
        </div>
      </div>
    );
  }

  // Recalculating score based on sliders in real-time
  const paceShift = (originalVals && optPace >= 3.5 && originalVals.pace < 2.5) ? 70 : (originalVals && optPace < 2.5 && originalVals.pace >= 3.5) ? -70 : 0;
  const crtShift = originalVals ? (optCRT - originalVals.crt) * 35 : 0;
  const consistencyShift = originalVals ? (optConsistency - originalVals.consistency) * 75 : 0;
  
  const adjustedScore = Math.max(300, Math.min(850, scoreData.credit_score + paceShift + crtShift + consistencyShift));
  const currentScore = simulatorTouched ? adjustedScore : scoreData.credit_score;
  const scoreToDisplay = (animationStep >= 3) ? currentScore : displayScore;
  const bandScore = animationStep >= 3 ? currentScore : scoreToDisplay;

  const repaymentProb = 0.35 + ((currentScore - 300) / 550) * 0.63;
  const percentile = Math.round(((currentScore - 300) / 550) * 98);
  const simulationChanged = simulatorTouched && currentScore !== scoreData.credit_score;
  const simulatedBandInfo = getBandInfoForScore(currentScore);
  const backendBandInfo = getBandInfoForScore(scoreData.credit_score);
  const backendEligibility = scoreData.loan_eligibility;
  const displayBand = animationStep >= 3
    ? (simulationChanged ? simulatedBandInfo.band : (scoreData.risk_band || backendBandInfo.band))
    : getBandInfoForScore(bandScore).band;
  const displayBandColor = animationStep >= 3
    ? (simulationChanged ? simulatedBandInfo.color : getBandColor(scoreData.risk_band, scoreData.credit_score))
    : getBandInfoForScore(bandScore).color;
  const displayBandShadow = animationStep >= 3
    ? (simulationChanged ? simulatedBandInfo.shadow : backendBandInfo.shadow)
    : getBandInfoForScore(bandScore).shadow;
  const displayMinAmount = simulationChanged ? simulatedBandInfo.loanMin : (backendEligibility?.amount_min ?? backendBandInfo.loanMin);
  const displayMaxAmount = simulationChanged ? simulatedBandInfo.loanMax : (backendEligibility?.amount_max ?? backendBandInfo.loanMax);
  const displayBandDesc = simulationChanged ? simulatedBandInfo.description : (backendEligibility?.description || backendBandInfo.description);
  const displayRepaymentProb = simulationChanged
    ? repaymentProb
    : (scoreData.repayment_probability ?? 0.35 + ((scoreData.credit_score - SCORE_MIN) / SCORE_RANGE) * 0.63);
  const displayPercentile = simulationChanged
    ? percentile
    : (scoreData.percentile ?? Math.round(((scoreData.credit_score - SCORE_MIN) / SCORE_RANGE) * 98));
  const explanationItems = asArray(scoreData.explanation);
  const counterfactualActions = asArray(scoreData.counterfactual_actions);
  const improvementTips = asArray(scoreData.improvement_tips);
  const maxAbsShap = Math.max(...explanationItems.map((item) => Math.abs(item.shap_value)), 1);
  const adjustPace = (delta) => {
    setSimulatorTouched(true);
    setOptPace((value) => clamp(Number((value + delta).toFixed(1)), 1, 8));
  };
  const adjustCRT = (delta) => {
    setSimulatorTouched(true);
    setOptCRT((value) => clamp(value + delta, 0, 2));
  };
  const adjustConsistency = (delta) => {
    setSimulatorTouched(true);
    setOptConsistency((value) => clamp(value + delta, 0, 1));
  };

  const ringOffsetToDisplay = (animationStep >= 3) 
    ? (440 - 440 * ((currentScore - 300) / 550)) 
    : ringOffset;

  return (
    <div className="results-layout">
      <div className="results-container container">
        
        {/* Cinematic Score Reveal Circle */}
        <section className="score-reveal-section">
          <div 
            className="score-circle-wrapper"
            style={{ 
              boxShadow: animationStep >= 3 ? displayBandShadow : 'none'
            }}
          >
            {/* SVG Circle Gauge */}
            <svg width="200" height="200" viewBox="0 0 200 200" className="score-svg">
              <circle
                cx="100"
                cy="100"
                r="70"
                fill="transparent"
                className="score-track"
              />
              <circle
                cx="100"
                cy="100"
                r="70"
                fill="transparent"
                className="score-progress"
                style={{
                  stroke: displayBandColor,
                  strokeDashoffset: ringOffsetToDisplay,
                  transition: 'stroke 0.4s ease, stroke-dashoffset 0.4s var(--ease-smooth)'
                }}
              />
            </svg>
            
            {/* Realtime Score Counter readout */}
            <div className="score-text-box">
              <span className="score-sub">Intel Score</span>
              <span className="score-num font-mono">{scoreToDisplay}</span>
              <span 
                className="score-band"
                style={{
                  color: displayBandColor,
                  textShadow: animationStep >= 3 ? `0 0 10px ${displayBandColor}40` : 'none'
                }}
              >
                <TextReveal text={formatBandLabel(displayBand)} />
              </span>
            </div>
          </div>

          <div 
            style={{ 
              opacity: animationStep >= 3 ? 1 : 0, 
              transform: animationStep >= 3 ? 'translateY(0)' : 'translateY(10px)',
              transition: 'all 500ms ease'
            }}
          >
            <p className="probability-label">{(displayRepaymentProb * 100).toFixed(1)}% Repayment Probability</p>
            <p className="percentile-label">Higher than {displayPercentile}% of cohort</p>
          </div>
        </section>

        {/* Info Grid (Bands & Loan Limits) */}
        <div className={`info-cards-row fade-in-content ${animationStep >= 4 ? 'visible' : ''}`}>
          <ScrollReveal direction="up" delay={100}>
            <GlowCard className="result-card">
              <span className="card-kicker">{simulationChanged ? 'Estimated Risk Assessment' : 'Risk Assessment'}</span>
              <h3 className="card-title">Band Verdict</h3>
              <p className="card-body">{displayBandDesc}</p>
            </GlowCard>
          </ScrollReveal>

          <ScrollReveal direction="up" delay={200}>
            <GlowCard className="result-card">
              <span className="card-kicker">Lending Access</span>
              <h3 className="card-title">Approved Loan Limit</h3>
              {displayMinAmount > 0 ? (
                <p className="loan-amount-range">
                  Rs. {displayMinAmount.toLocaleString('en-IN')} - Rs. {displayMaxAmount.toLocaleString('en-IN')}
                </p>
              ) : (
                <p className="loan-amount-range" style={{ color: 'var(--accent-rose)' }}>Deferred</p>
              )}
              <p className="card-body">
                {simulationChanged ? 'Estimated from simulator adjustments.' : 'Subject to lender policy and telemetry consistency.'}
              </p>
            </GlowCard>
          </ScrollReveal>
        </div>

        {/* SHAP Feature Contribution Bars */}
        <ScrollReveal direction="up" delay={300}>
          <section className={`shap-panel fade-in-content ${animationStep >= 4 ? 'visible' : ''}`}>
            <div className="results-section-header">
              <span className="section-eyebrow">Explainable AI</span>
              <h2 className="results-section-title">
                <TextReveal text="What Drove Your Score" />
              </h2>
            </div>

            <GlowCard className="shap-table result-card">
              {explanationItems.map((item, idx) => {
                const isPos = item.direction === 'positive';
                const percentage = Math.min((Math.abs(item.shap_value) / maxAbsShap) * 100, 100);
                
                return (
                  <div key={idx} className="shap-row">
                    <span className="shap-feature-name">{item.display_name}</span>
                    <div className="shap-bar-container">
                      <div 
                        className={`shap-bar-fill loaded shimmer-bg`}
                        style={{ 
                          width: `${percentage}%`,
                          backgroundColor: isPos ? 'var(--accent-emerald)' : 'var(--accent-rose)',
                        }}
                      />
                    </div>
                    <span className={`shap-value-badge ${isPos ? 'positive' : 'negative'}`}>
                      {isPos ? '+' : ''}{item.shap_value.toFixed(2)}
                    </span>
                  </div>
                );
              })}
            </GlowCard>
          </section>
        </ScrollReveal>

        {/* SCORE OPTIMIZER PLAYGROUND WIDGET */}
        <ScrollReveal direction="up" delay={400}>
          <section className={`optimizer-widget fade-in-content ${animationStep >= 4 ? 'visible' : ''}`}>
            <div className="optimizer-header">
              <h3 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px', margin: 0, fontSize: '15px' }}>
                <Sliders size={16} style={{ color: 'var(--accent-cyan)' }} />
                <span>Score Optimizer Playground</span>
              </h3>
              <span className="optimizer-tag">Simulation HUD</span>
            </div>

            <div className="optimizer-sliders">
              <div className="slider-group">
                <div className="slider-label-row">
                  <span className="slider-name">Deliberation Pace (Average response time)</span>
                  <span className="slider-val">
                    {optPace.toFixed(1)}s {optPace < 2.5 ? '(Rapid/Gaming Flag)' : '(Deliberate)'}
                  </span>
                </div>
                <div className="range-control-row">
                  <button type="button" className="range-stepper" onClick={() => adjustPace(-0.5)} aria-label="Decrease deliberation pace">
                    <Minus size={14} />
                  </button>
                  <input
                    type="range"
                    min="1.0"
                    max="8.0"
                    step="0.5"
                    value={optPace}
                    onChange={(e) => {
                      setSimulatorTouched(true);
                      setOptPace(parseFloat(e.target.value));
                    }}
                    className="input-range-control"
                    aria-label="Deliberation pace"
                    aria-valuetext={`${optPace.toFixed(1)} seconds`}
                  />
                  <button type="button" className="range-stepper" onClick={() => adjustPace(0.5)} aria-label="Increase deliberation pace">
                    <Plus size={14} />
                  </button>
                </div>
              </div>

              <div className="slider-group">
                <div className="slider-label-row">
                  <span className="slider-name">Cognitive Reflection (CRT correctness)</span>
                  <span className="slider-val">{optCRT} / 2 Correct</span>
                </div>
                <div className="range-control-row">
                  <button type="button" className="range-stepper" onClick={() => adjustCRT(-1)} aria-label="Decrease cognitive reflection correctness">
                    <Minus size={14} />
                  </button>
                  <input
                    type="range"
                    min="0"
                    max="2"
                    step="1"
                    value={optCRT}
                    onChange={(e) => {
                      setSimulatorTouched(true);
                      setOptCRT(parseInt(e.target.value));
                    }}
                    className="input-range-control"
                    aria-label="Cognitive reflection correctness"
                    aria-valuetext={`${optCRT} of 2 correct`}
                  />
                  <button type="button" className="range-stepper" onClick={() => adjustCRT(1)} aria-label="Increase cognitive reflection correctness">
                    <Plus size={14} />
                  </button>
                </div>
              </div>

              <div className="slider-group">
                <div className="slider-label-row">
                  <span className="slider-name">Decision Frame Consistency (Matched trap questions)</span>
                  <span className="slider-val">
                    {optConsistency === 1 ? '100% Consistent (Match)' : '0% Consistent (Gaming Flag)'}
                  </span>
                </div>
                <div className="range-control-row">
                  <button type="button" className="range-stepper" onClick={() => adjustConsistency(-1)} aria-label="Decrease decision frame consistency">
                    <Minus size={14} />
                  </button>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="1"
                    value={optConsistency}
                    onChange={(e) => {
                      setSimulatorTouched(true);
                      setOptConsistency(parseInt(e.target.value));
                    }}
                    className="input-range-control"
                    aria-label="Decision frame consistency"
                    aria-valuetext={optConsistency === 1 ? 'Consistent match' : 'Mismatch flag'}
                  />
                  <button type="button" className="range-stepper" onClick={() => adjustConsistency(1)} aria-label="Increase decision frame consistency">
                    <Plus size={14} />
                  </button>
                </div>
              </div>
            </div>

            <div className="optimizer-summary">
              <p>
                *Simulating behavioral adjustments calculates shifts against the Stacking Calibration pipeline. Increasing deliberation times above 3.5s and completing the matching scenarios consistently eliminates system flags.
              </p>
            </div>
          </section>
        </ScrollReveal>

        {/* DiCE-ML Counterfactual Suggestions */}
        <section className={`dice-panel fade-in-content ${animationStep >= 4 ? 'visible' : ''}`}>
          <div className="results-section-header">
            <span className="section-eyebrow">Counterfactual Recommendations</span>
            <h2 className="results-section-title">
              <TextReveal text="What Could Move You Up" />
            </h2>
          </div>

          <div className="dice-list">
            {counterfactualActions.map((act, idx) => (
              <ScrollReveal direction="scale" delay={idx * 100} key={idx}>
                <GlowCard className="dice-card">
                  <span className="dice-feature-change">
                    Gain: +{act.estimated_score_gain} Pts
                  </span>
                  <span className="dice-description">{act.plain_language}</span>
                </GlowCard>
              </ScrollReveal>
            ))}
          </div>
        </section>

        {/* Improvement tips */}
        <section className={`tips-panel fade-in-content ${animationStep >= 4 ? 'visible' : ''}`}>
          <div className="results-section-header">
            <span className="section-eyebrow">Pacing Guides</span>
            <h2 className="results-section-title">
              <TextReveal text="System Guidance Tips" />
            </h2>
          </div>

          <div className="tips-list">
            {improvementTips.map((tip, idx) => (
              <ScrollReveal direction="scale" delay={idx * 100} key={idx}>
                <GlowCard className="tip-card">
                  <h4 className="tip-header">{tip.title}</h4>
                  <p className="tip-body">{tip.body}</p>
                </GlowCard>
              </ScrollReveal>
            ))}
          </div>
        </section>

        {/* Navigation CTAs */}
        <div className={`actions-row fade-in-content ${animationStep >= 4 ? 'visible' : ''}`}>
          <ScrollReveal direction="up" delay={100}>
            <button onClick={() => { playClick(); transitionTo('/assessment'); }} className="btn btn-ghost">
              <RotateCcw size={14} />
              <span>Retake Assessment</span>
            </button>
          </ScrollReveal>

          <ScrollReveal direction="up" delay={200}>
            <button onClick={() => { playClick(); transitionTo('/dashboard'); }} className="btn btn-primary">
              <LayoutDashboard size={14} />
              <span>Analytics Dashboard</span>
            </button>
          </ScrollReveal>
        </div>

      </div>
    </div>
  );
}
