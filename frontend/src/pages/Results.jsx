import { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { Sliders, RotateCcw, LayoutDashboard, AlertCircle } from 'lucide-react';
import ScrollReveal from '../components/animation/ScrollReveal';
import GlowCard from '../components/ui/GlowCard';
import TextReveal from '../components/animation/TextReveal';
import useSound from '../hooks/useSound';
import usePageTransition from '../hooks/usePageTransition';
import './Results.css';

export default function Results() {
  const location = useLocation();
  const { transitionTo } = usePageTransition();
  const { playSuccess, playClick } = useSound();
  
  const scoreData = location.state;
  
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

  // Derived slider metrics based on user's actual choices
  const [originalVals] = useState(() => {
    if (!scoreData) return null;
    const isGaming = scoreData.credit_score < 400 && scoreData.explanation.some(e => e.feature === 'avg_response_time_ms' && e.shap_value < 0);
    const isCRTCorrect = scoreData.explanation.some(e => e.feature === 'CRT_score' && e.shap_value > 0);
    const isConsistent = scoreData.explanation.some(e => e.feature === 'scenario_consistency_score' && e.shap_value > 0);
    return {
      pace: isGaming ? 1.5 : 5.0,
      crt: isCRTCorrect ? 2 : 0,
      consistency: isConsistent ? 1 : 0
    };
  });

  // Interactive Optimizer Playground State
  const [optPace, setOptPace] = useState(() => originalVals?.pace ?? 5.0); // response pace in seconds
  const [optCRT, setOptCRT] = useState(() => originalVals?.crt ?? 0); // CRT answers correct (0-2)
  const [optConsistency, setOptConsistency] = useState(() => originalVals?.consistency ?? 0); // 0 (mismatch) or 1 (match)

  // Trigger Cinematic Reveal Animation
  useEffect(() => {
    if (!scoreData) return;
    const t1 = setTimeout(() => {
      setAnimationStep(1);
      const percentage = (scoreData.credit_score - 300) / 550;
      setRingOffset(440 - 440 * percentage);
    }, 200);

    const t2 = setTimeout(() => {
      setAnimationStep(2);
      const target = scoreData.credit_score;
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
      playSuccess(); // Play cinematic sound chord when glow pops!
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
  }, [scoreData, playSuccess]);

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
  
  const currentScore = Math.max(300, Math.min(850, scoreData.credit_score + paceShift + crtShift + consistencyShift));

  // Recalculate bands and numbers based on currentScore
  let band;
  let bandColor;
  let bandShadow;
  let minAmount;
  let maxAmount;
  let bandDesc;

  if (currentScore >= 750) {
    band = 'excellent';
    bandColor = 'var(--score-excellent)';
    bandShadow = 'var(--shadow-score-excellent)';
    minAmount = 30000;
    maxAmount = 75000;
    bandDesc = 'Microloans up to ₹75,000 approved. Extremely low default probability.';
  } else if (currentScore >= 650) {
    band = 'good';
    bandColor = 'var(--score-good)';
    bandShadow = 'var(--shadow-score-good)';
    minAmount = 12000;
    maxAmount = 30000;
    bandDesc = 'Microloans up to ₹30,000 approved. Solid repayment probability.';
  } else if (currentScore >= 550) {
    band = 'fair';
    bandColor = 'var(--score-fair)';
    bandShadow = 'var(--shadow-score-fair)';
    minAmount = 5000;
    maxAmount = 12000;
    bandDesc = 'Microloans up to ₹12,000 approved. Moderate risk conditions apply.';
  } else if (currentScore >= 450) {
    band = 'poor';
    bandColor = 'var(--score-poor)';
    bandShadow = 'var(--shadow-score-poor)';
    minAmount = 2000;
    maxAmount = 5000;
    bandDesc = 'Microloans up to ₹5,000 approved. Sub-prime risk controls active.';
  } else {
    band = 'very_poor';
    bandColor = 'var(--score-very-poor)';
    bandShadow = 'var(--shadow-score-very-poor)';
    minAmount = 0;
    maxAmount = 0;
    bandDesc = 'Funding deferred. Score below threshold. Credit counselling recommended.';
  }

  const repaymentProb = 0.35 + ((currentScore - 300) / 550) * 0.63;
  const percentile = Math.round(((currentScore - 300) / 550) * 98);

  const scoreToDisplay = (animationStep >= 3) ? currentScore : displayScore;
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
              boxShadow: animationStep >= 3 ? bandShadow : 'none'
            }}
          >
            {/* SVG Circle Gauge */}
            <svg width="200" height="200" className="score-svg">
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
                  stroke: bandColor,
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
                  color: bandColor,
                  textShadow: animationStep >= 3 ? `0 0 10px ${bandColor}40` : 'none'
                }}
              >
                <TextReveal text={band} />
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
            <p className="probability-label">{(repaymentProb * 100).toFixed(1)}% Repayment Probability</p>
            <p className="percentile-label">Higher than {percentile}% of cohort</p>
          </div>
        </section>

        {/* Info Grid (Bands & Loan Limits) */}
        <div className={`info-cards-row fade-in-content ${animationStep >= 4 ? 'visible' : ''}`}>
          <ScrollReveal direction="up" delay={100}>
            <GlowCard className="result-card">
              <span className="card-kicker">Risk Assessment</span>
              <h3 className="card-title">Band Verdict</h3>
              <p className="card-body">{bandDesc}</p>
            </GlowCard>
          </ScrollReveal>

          <ScrollReveal direction="up" delay={200}>
            <GlowCard className="result-card">
              <span className="card-kicker">Lending Access</span>
              <h3 className="card-title">Approved Loan Limit</h3>
              {minAmount > 0 ? (
                <p className="loan-amount-range">
                  ₹{minAmount.toLocaleString('en-IN')} – ₹{maxAmount.toLocaleString('en-IN')}
                </p>
              ) : (
                <p className="loan-amount-range" style={{ color: 'var(--accent-rose)' }}>Deferred</p>
              )}
              <p className="card-body">Subject to telemetry consistency.</p>
            </GlowCard>
          </ScrollReveal>
        </div>

        {/* SHAP Feature Contribution Bars */}
        <ScrollReveal direction="up" delay={300}>
          <section className={`shap-panel fade-in-content ${animationStep >= 4 ? 'visible' : ''}`}>
            <div className="section-header" style={{ textAlign: 'left', marginBottom: '24px' }}>
              <span className="section-eyebrow">Explainable AI</span>
              <h2 className="section-title" style={{ fontSize: 'var(--text-xl)' }}>
                <TextReveal text="What Drove Your Score" />
              </h2>
            </div>

            <GlowCard className="shap-table result-card">
              {scoreData.explanation.map((item, idx) => {
                const isPos = item.direction === 'positive';
                const maxShap = 0.15; // normalize max bar width
                const percentage = Math.min((Math.abs(item.shap_value) / maxShap) * 100, 100);
                
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
                      {isPos ? '+' : ''}{Math.round(item.shap_value * 1000)} pts
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
                <input
                  type="range"
                  min="1.0"
                  max="8.0"
                  step="0.5"
                  value={optPace}
                  onChange={(e) => setOptPace(parseFloat(e.target.value))}
                  className="optimizer-input-range"
                />
              </div>

              <div className="slider-group">
                <div className="slider-label-row">
                  <span className="slider-name">Cognitive Reflection (CRT correctness)</span>
                  <span className="slider-val">{optCRT} / 2 Correct</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="2"
                  step="1"
                  value={optCRT}
                  onChange={(e) => setOptCRT(parseInt(e.target.value))}
                  className="optimizer-input-range"
                />
              </div>

              <div className="slider-group">
                <div className="slider-label-row">
                  <span className="slider-name">Decision Frame Consistency (Matched trap questions)</span>
                  <span className="slider-val">
                    {optConsistency === 1 ? '100% Consistent (Match)' : '0% Mismatch (Gaming Flag)'}
                  </span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="1"
                  value={optConsistency}
                  onChange={(e) => setOptConsistency(parseInt(e.target.value))}
                  className="optimizer-input-range"
                />
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
          <div className="section-header" style={{ textAlign: 'left', marginBottom: '24px' }}>
            <span className="section-eyebrow">Counterfactual Recommendations</span>
            <h2 className="section-title" style={{ fontSize: 'var(--text-xl)' }}>
              <TextReveal text="What Could Move You Up" />
            </h2>
          </div>

          <div className="dice-list">
            {scoreData.counterfactual_actions.map((act, idx) => (
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
          <div className="section-header" style={{ textAlign: 'left', marginBottom: '24px' }}>
            <span className="section-eyebrow">Pacing Guides</span>
            <h2 className="section-title" style={{ fontSize: 'var(--text-xl)' }}>
              <TextReveal text="System Guidance Tips" />
            </h2>
          </div>

          <div className="tips-list">
            {scoreData.improvement_tips.map((tip, idx) => (
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
