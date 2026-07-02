import { useState } from 'react';
import { XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Cell } from 'recharts';
import { Activity, Sliders, ArrowLeft, RotateCcw, ShieldCheck, Sparkles, AlertCircle, Minus, Plus } from 'lucide-react';
import ScrollReveal from '../components/animation/ScrollReveal';
import GlowCard from '../components/ui/GlowCard';
import TextReveal from '../components/animation/TextReveal';
import useSound from '../hooks/useSound';
import usePageTransition from '../hooks/usePageTransition';
import './Dashboard.css';

function asArray(value) {
  return Array.isArray(value) ? value : [];
}

function formatBandLabel(band) {
  return String(band || '')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function formatOrdinal(value) {
  const number = Math.round(Number(value) || 0);
  const mod100 = number % 100;
  if (mod100 >= 11 && mod100 <= 13) return `${number}th`;

  switch (number % 10) {
    case 1:
      return `${number}st`;
    case 2:
      return `${number}nd`;
    case 3:
      return `${number}rd`;
    default:
      return `${number}th`;
  }
}

function getBandInfo(score, backendBand, backendDescription) {
  const normalizedBand = String(backendBand || '').toLowerCase();
  const scoreBand = score >= 750 ? 'excellent' : score >= 650 ? 'good' : score >= 550 ? 'fair' : score >= 450 ? 'poor' : 'very_poor';
  const band = ['excellent', 'good', 'fair', 'poor', 'very_poor'].includes(normalizedBand)
    ? normalizedBand
    : scoreBand;

  const infoByBand = {
    excellent: { color: 'var(--score-excellent)', shadow: 'var(--shadow-score-excellent)', desc: 'Excellent behavioral rating. Prime lending access approved.' },
    good: { color: 'var(--score-good)', shadow: 'var(--shadow-score-good)', desc: 'Solid consistency and deliberate pacing. Standard microcredit active.' },
    fair: { color: 'var(--score-fair)', shadow: 'var(--shadow-score-fair)', desc: 'Moderate rating. Minor pacing drift detected.' },
    poor: { color: 'var(--score-poor)', shadow: 'var(--shadow-score-poor)', desc: 'Limited eligibility; financial coaching is recommended before larger borrowing.' },
    very_poor: { color: 'var(--score-very-poor)', shadow: 'var(--shadow-score-very-poor)', desc: 'Funding deferred. Score below threshold. Credit counselling recommended.' },
  };

  return {
    label: band,
    ...infoByBand[band],
    desc: backendDescription || infoByBand[band].desc,
  };
}

function getSimulatorDefaults(data) {
  if (!data) {
    return { pace: 4.0, consistency: 1.0, focus: 0.5 };
  }

  const governance = data.governance_signals || {};
  const explanation = asArray(data.explanation);
  const hasPaceDrag = explanation.some(
    (item) => item.feature === 'avg_response_time_ms' && item.direction === 'negative' && Number(item.shap_value) < 0
  );
  const hasConsistencyDrag = explanation.some(
    (item) => item.feature === 'scenario_consistency_score' && Number(item.shap_value) < 0
  );
  const hasFocusLift = explanation.some(
    (item) => item.feature === 'CRT_score' && Number(item.shap_value) > 0
  );

  return {
    pace: governance.scenario_fast_gaming || hasPaceDrag ? 1.5 : 5.0,
    consistency:
      typeof governance.scenario_consistency_score === 'number'
        ? (governance.scenario_consistency_score >= 0.9 ? 1.0 : 0.5)
        : (hasConsistencyDrag ? 0.5 : 1.0),
    focus: hasFocusLift ? 0.75 : 0.5,
  };
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

export default function Dashboard() {
  const { transitionTo } = usePageTransition();
  const { playClick, playSelect } = useSound();

  // Load results from localStorage
  const [scoreData] = useState(() => {
    const saved = localStorage.getItem('alterscore_results');
    if (!saved) return null;

    try {
      return JSON.parse(saved);
    } catch {
      return null;
    }
  });

  const [demoMode, setDemoMode] = useState(false);

  // Default Demo Score Data if user hasn't taken the assessment
  const demoScoreData = {
    credit_score: 712,
    repayment_probability: 0.825,
    percentile: 74,
    explanation: [
      { feature: 'future_orientation_score', display_name: 'Future Orientation', shap_value: 0.083, direction: 'positive' },
      { feature: 'scenario_consistency_score', display_name: 'Choice Consistency', shap_value: 0.065, direction: 'positive' },
      { feature: 'avg_response_time_ms', display_name: 'Deliberation Pace', shap_value: -0.012, direction: 'negative' },
      { feature: 'CRT_score', display_name: 'Cognitive Reflection', shap_value: 0.035, direction: 'positive' }
    ],
    counterfactual_actions: [
      { estimated_score_gain: 45, plain_language: 'Take 2.5s longer to reflection-check math puzzles before answering.' },
      { estimated_score_gain: 30, plain_language: 'Maintain identical choice selection on duplicate scenario frames.' }
    ],
    improvement_tips: [
      { title: 'Reduce Decision Variance', body: 'Avoid rushing through similar-looking scenarios; consistency is highly rated by the ensemble.' },
      { title: 'Deliberation Timing', body: 'Spending at least 4.0 seconds on complex scenarios signals cognitive focus rather than random clicks.' }
    ]
  };

  const activeData = scoreData || (demoMode ? demoScoreData : null);
  const simulatorDefaults = getSimulatorDefaults(activeData);

  // Interactive Simulator Sliders
  const [simulatorTouched, setSimulatorTouched] = useState(false);
  const [simPace, setSimPace] = useState(simulatorDefaults.pace);
  const [simConsistency, setSimConsistency] = useState(simulatorDefaults.consistency);
  const [simFocus, setSimFocus] = useState(simulatorDefaults.focus);

  
  const originalScore = activeData ? activeData.credit_score : 580;

  // Recalculate score based on simulator sliders
  const paceShift = simPace < 2.5 ? -70 : simPace > 4.5 ? 40 : 0;
  const consistencyShift = (simConsistency - 1.0) * 120; // drop if inconsistent
  const focusShift = Math.round((simFocus - 0.5) * 80); // shift up/down based on focus
  
  const simulatedScore = Math.max(300, Math.min(850, originalScore + paceShift + consistencyShift + focusShift));
  const currentScore = simulatorTouched ? simulatedScore : originalScore;
  const displayRepaymentProbability = simulatorTouched
    ? 0.35 + ((currentScore - 300) / 550) * 0.63
    : (activeData?.repayment_probability ?? 0.35 + ((currentScore - 300) / 550) * 0.63);
  const displayPercentile = simulatorTouched
    ? Math.round(((currentScore - 300) / 550) * 98)
    : (activeData?.percentile ?? Math.round(((currentScore - 300) / 550) * 98));

  const bandInfo = getBandInfo(
    currentScore,
    simulatorTouched ? null : activeData?.risk_band,
    simulatorTouched ? null : activeData?.loan_eligibility?.description
  );
  const actionItems = asArray(activeData?.counterfactual_actions);

  const scoreDistribution = [
    { name: '300-349', count: 36, fill: 'var(--score-very-poor)' },
    { name: '350-399', count: 85, fill: 'var(--score-very-poor)' },
    { name: '400-449', count: 124, fill: 'var(--score-very-poor)' },
    { name: '450-499', count: 180, fill: 'var(--score-poor)' },
    { name: '500-549', count: 240, fill: 'var(--score-poor)' },
    { name: '550-599', count: 320, fill: 'var(--score-fair)' },
    { name: '600-649', count: 375, fill: 'var(--score-fair)' },
    { name: '650-699', count: 290, fill: 'var(--score-good)' },
    { name: '700-749', count: 210, fill: 'var(--score-good)' },
    { name: '750-799', count: 110, fill: 'var(--score-excellent)' },
    { name: '800-850', count: 42, fill: 'var(--score-excellent)' }
  ];

  // SVG Circle Gauge dashoffset
  const ringOffset = 440 - 440 * ((currentScore - 300) / 550);

  const enableDemo = () => {
    const demoDefaults = getSimulatorDefaults(demoScoreData);
    playClick();
    setSimulatorTouched(false);
    setSimPace(demoDefaults.pace);
    setSimConsistency(demoDefaults.consistency);
    setSimFocus(demoDefaults.focus);
    setDemoMode(true);
  };

  const clearDemo = () => {
    const savedDefaults = getSimulatorDefaults(scoreData);
    setDemoMode(false);
    setSimulatorTouched(false);
    setSimPace(savedDefaults.pace);
    setSimConsistency(savedDefaults.consistency);
    setSimFocus(savedDefaults.focus);
  };
  const adjustPace = (delta) => {
    setSimulatorTouched(true);
    setSimPace((value) => clamp(Number((value + delta).toFixed(1)), 1, 8));
    playSelect();
  };
  const adjustConsistency = (delta) => {
    setSimulatorTouched(true);
    setSimConsistency((value) => clamp(Number((value + delta).toFixed(1)), 0.5, 1));
    playSelect();
  };
  const adjustFocus = (delta) => {
    setSimulatorTouched(true);
    setSimFocus((value) => clamp(Number((value + delta).toFixed(2)), 0.4, 1));
    playSelect();
  };

  if (!activeData) {
    return (
      <div className="dashboard-blank-state">
        <div className="blank-state-card glass font-mono">
          <AlertCircle size={48} style={{ color: 'var(--accent-cyan)', marginBottom: '16px' }} />
          <h2>No Active Score Profile</h2>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '24px', fontSize: '13px', lineHeight: 1.6 }}>
            You haven't completed the psychometric assessment yet. Generate your behavioral credit intelligence score to view personal metrics.
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <button onClick={() => transitionTo('/assessment')} className="btn btn-primary" style={{ width: '100%' }}>
              <span>Start Assessment</span>
            </button>
            <button onClick={enableDemo} className="btn btn-ghost" style={{ width: '100%', borderColor: 'rgba(255,255,255,0.06)' }}>
              <span>Explore Demo Profile</span>
            </button>
          </div>
        </div>
        
        {/* Blurred Dashboard Mockup in background */}
        <div className="dashboard-layout blurred" style={{ filter: 'blur(16px)', pointerEvents: 'none' }}>
          <aside className="dashboard-sidebar" />
          <main className="dashboard-content" />
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-layout">
      {/* Sidebar Navigation */}
      <aside className="dashboard-sidebar">
        <div className="sidebar-title">
          <Activity size={18} style={{ color: 'var(--accent-cyan)' }} />
          <span>AlterScore Portal</span>
        </div>
        <nav className="sidebar-menu">
          <button onClick={() => transitionTo('/')} className="sidebar-item btn-sidebar-action" aria-label="Go to home">
            <ArrowLeft size={16} />
            <span>Home</span>
          </button>
          <button onClick={() => transitionTo('/assessment')} className="sidebar-item btn-sidebar-action" aria-label="Retake assessment">
            <RotateCcw size={16} />
            <span>Retake Test</span>
          </button>
          <div className="sidebar-item active">
            <ShieldCheck size={16} />
            <span>My Score Profile</span>
          </div>
        </nav>
        {demoMode && (
          <div className="demo-badge-sidebar font-mono">
            <span>DEMO PROFILE ACTIVE</span>
            <button onClick={clearDemo} className="btn-exit-demo">
              Clear
            </button>
          </div>
        )}
        <div className="sidebar-footer">
          <p>© AlterScore</p>
          <p style={{ opacity: 0.4, marginTop: '2px' }}>v2.0.0-PROD</p>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="dashboard-content">
        <header className="dashboard-header">
          <span className="dashboard-subtitle">Personal Intelligence Console</span>
          <h1 className="dashboard-title">
            <TextReveal text="My Credit Analytics" />
          </h1>
        </header>

        {demoMode && (
          <div className="demo-banner-mobile font-mono">
            <span>DEMO PROFILE ACTIVE</span>
            <button onClick={clearDemo} className="btn-exit-demo">
              Clear
            </button>
          </div>
        )}

        {/* Dashboard Grid Layout */}
        <div className="dashboard-grid">
          
          {/* Hero Score Gauge Card */}
          <ScrollReveal direction="up" delay={50}>
            <GlowCard className="dashboard-hero-card">
              <div className="hero-card-left">
                <span className="section-eyebrow">Behavioral Rating</span>
                <h2 className="hero-card-title">Score Verdict</h2>
                <p className="hero-card-desc" style={{ color: bandInfo.color }}>
                  {bandInfo.desc}
                </p>
                <div className="hero-metrics-row">
                  <div className="hero-metric-item">
                    <span className="hero-metric-label">Repayment Probability</span>
                    <span className="hero-metric-val font-mono">
                      {(displayRepaymentProbability * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="hero-metric-item">
                    <span className="hero-metric-label">Cohort Percentile</span>
                    <span className="hero-metric-val font-mono">
                      {formatOrdinal(displayPercentile)}
                    </span>
                  </div>
                </div>
              </div>

              <div className="hero-card-right">
                <div 
                  className="dashboard-circle-wrapper"
                  style={{ boxShadow: bandInfo.shadow }}
                >
                  <svg width="180" height="180" className="dashboard-score-svg">
                    <circle cx="90" cy="90" r="70" fill="transparent" className="dashboard-score-track" />
                    <circle 
                      cx="90" 
                      cy="90" 
                      r="70" 
                      fill="transparent" 
                      className="dashboard-score-progress"
                      style={{
                        stroke: bandInfo.color,
                        strokeDashoffset: ringOffset,
                        transition: 'stroke 0.4s ease, stroke-dashoffset 0.4s var(--ease-smooth)'
                      }}
                    />
                  </svg>
                  <div className="dashboard-score-text">
                    <span className="db-score-num font-mono">{currentScore}</span>
                    <span className="db-score-lbl" style={{ color: bandInfo.color }}>
                      {formatBandLabel(bandInfo.label)}
                    </span>
                  </div>
                </div>
              </div>
            </GlowCard>
          </ScrollReveal>

          {/* Interactive Trait Simulator */}
          <ScrollReveal direction="up" delay={150}>
            <GlowCard className="dashboard-panel-card">
              <div className="panel-header">
                <h3 className="panel-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Sliders size={16} style={{ color: 'var(--accent-cyan)' }} />
                  <span>Interactive Credit Simulator</span>
                </h3>
                <span className={`panel-badge ${simulatorTouched ? 'panel-badge-active' : ''}`}>
                  {simulatorTouched ? 'Simulation Mode' : 'Saved Result'}
                </span>
              </div>
              <div className="simulator-body">
                <div className="sim-sliders-col">
                  <div className="slider-group">
                    <div className="slider-label-row">
                      <span className="slider-name">Deliberation Pace (Avg RT)</span>
                      <span className="slider-val font-mono">{simPace.toFixed(1)}s</span>
                    </div>
                    <div className="range-control-row">
                      <button type="button" className="range-stepper" onClick={() => adjustPace(-0.5)} aria-label="Decrease simulator deliberation pace">
                        <Minus size={14} />
                      </button>
                      <input
                        type="range"
                        min="1.0"
                        max="8.0"
                        step="0.5"
                        value={simPace}
                        onChange={(e) => {
                          setSimulatorTouched(true);
                          setSimPace(parseFloat(e.target.value));
                          playSelect();
                        }}
                        className="input-range-control"
                        aria-label="Simulator deliberation pace"
                        aria-valuetext={`${simPace.toFixed(1)} seconds`}
                      />
                      <button type="button" className="range-stepper" onClick={() => adjustPace(0.5)} aria-label="Increase simulator deliberation pace">
                        <Plus size={14} />
                      </button>
                    </div>
                  </div>

                  <div className="slider-group">
                    <div className="slider-label-row">
                      <span className="slider-name">Choice Consistency</span>
                      <span className="slider-val font-mono">
                        {simConsistency === 1.0 ? 'Consistent (100%)' : 'Variance / Drift (50%)'}
                      </span>
                    </div>
                    <div className="range-control-row">
                      <button type="button" className="range-stepper" onClick={() => adjustConsistency(-0.5)} aria-label="Decrease simulator choice consistency">
                        <Minus size={14} />
                      </button>
                      <input
                        type="range"
                        min="0.5"
                        max="1.0"
                        step="0.5"
                        value={simConsistency}
                        onChange={(e) => {
                          setSimulatorTouched(true);
                          setSimConsistency(parseFloat(e.target.value));
                          playSelect();
                        }}
                        className="input-range-control"
                        aria-label="Simulator choice consistency"
                        aria-valuetext={simConsistency === 1.0 ? 'Consistent, 100 percent' : 'Variance drift, 50 percent'}
                      />
                      <button type="button" className="range-stepper" onClick={() => adjustConsistency(0.5)} aria-label="Increase simulator choice consistency">
                        <Plus size={14} />
                      </button>
                    </div>
                  </div>

                  <div className="slider-group">
                    <div className="slider-label-row">
                      <span className="slider-name">Reflection Focus</span>
                      <span className="slider-val font-mono">{Math.round(simFocus * 100)}%</span>
                    </div>
                    <div className="range-control-row">
                      <button type="button" className="range-stepper" onClick={() => adjustFocus(-0.05)} aria-label="Decrease simulator reflection focus">
                        <Minus size={14} />
                      </button>
                      <input
                        type="range"
                        min="0.4"
                        max="1.0"
                        step="0.05"
                        value={simFocus}
                        onChange={(e) => {
                          setSimulatorTouched(true);
                          setSimFocus(parseFloat(e.target.value));
                          playSelect();
                        }}
                        className="input-range-control"
                        aria-label="Simulator reflection focus"
                        aria-valuetext={`${Math.round(simFocus * 100)} percent`}
                      />
                      <button type="button" className="range-stepper" onClick={() => adjustFocus(0.05)} aria-label="Increase simulator reflection focus">
                        <Plus size={14} />
                      </button>
                    </div>
                  </div>
                </div>

                <div className="sim-explanations-col font-mono">
                  <div className="sim-advice-box">
                    <Sparkles size={14} className="advice-icon" />
                    <span>Simulator Insights:</span>
                    <p style={{ marginTop: '8px', color: 'var(--text-secondary)', fontSize: '11px', lineHeight: 1.5 }}>
                      {paceShift < 0
                        ? '! Rapid pacing under 2.5s triggers automation-flag warnings.'
                        : 'OK: Deliberate pacing above 3.5s satisfies logical calibration standards.'}
                      <br />
                      {consistencyShift < 0
                        ? '! Decision variance indicates erratic response strategies (-120 pts).'
                        : 'OK: Matched scenario patterns satisfy integrity checks (+0 pts).'}
                      <br />
                      {focusShift >= 0
                        ? `OK: Focus rating of ${Math.round(simFocus * 100)}% adds +${focusShift} pts.`
                        : `! Lower focus decreases score by ${Math.abs(focusShift)} pts.`}
                    </p>
                  </div>
                </div>
              </div>
            </GlowCard>
          </ScrollReveal>

          {/* Grid section for Stats & Trait Bars */}
          <div className="grid-6-6">
            
            {/* User Friendly Behavioral Traits */}
            <ScrollReveal direction="left" delay={200}>
              <GlowCard className="dashboard-panel-card">
                <div className="panel-header">
                  <h3 className="panel-title">My Behavioral Indices</h3>
                  <span className="panel-badge">Telemetry profile</span>
                </div>
                <div className="dashboard-trait-table">
                  <div className="dashboard-trait-row">
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      <span className="dashboard-trait-name">Deliberation index</span>
                      <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Pace of decision-making reflection vs. impulsivity</span>
                    </div>
                    <div className="trait-progress-wrapper">
                      <div className="dashboard-trait-progress">
                        <div 
                          className="dashboard-trait-progress-fill"
                          style={{ width: `${Math.round(simPace / 8 * 100)}%`, backgroundColor: 'var(--accent-cyan)' }} 
                        />
                      </div>
                    </div>
                  </div>

                  <div className="dashboard-trait-row">
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      <span className="dashboard-trait-name">Choice Integrity</span>
                      <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Consistency when matching questions are re-framed</span>
                    </div>
                    <div className="trait-progress-wrapper">
                      <div className="dashboard-trait-progress">
                        <div 
                          className="dashboard-trait-progress-fill"
                          style={{ width: `${simConsistency * 100}%`, backgroundColor: 'var(--accent-emerald)' }} 
                        />
                      </div>
                    </div>
                  </div>

                  <div className="dashboard-trait-row">
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      <span className="dashboard-trait-name">Stress Resilience</span>
                      <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Contingency planning and recovery preferences</span>
                    </div>
                    <div className="trait-progress-wrapper">
                      <div className="dashboard-trait-progress">
                        <div 
                          className="dashboard-trait-progress-fill"
                          style={{ width: `${Math.round(simFocus * 100)}%`, backgroundColor: 'var(--accent-amber)' }} 
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </GlowCard>
            </ScrollReveal>

            {/* Score Distribution Chart */}
            <ScrollReveal direction="right" delay={200}>
              <GlowCard className="dashboard-panel-card">
                <div className="panel-header">
                  <h3 className="panel-title">Population Score Distribution</h3>
                  <span className="panel-badge">My Position</span>
                </div>
                <div className="chart-container" style={{ height: '180px' }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={scoreDistribution}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.02)" />
                      <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={8} />
                      <YAxis stroke="var(--text-muted)" fontSize={8} />
                      <Tooltip contentStyle={{ background: '#0B1221', border: '1px solid var(--bg-border)', fontSize: '10px' }} />
                      <Bar dataKey="count" fill="var(--bg-muted)" radius={[2, 2, 0, 0]}>
                        {scoreDistribution.map((entry, idx) => {
                          // Determine if this bar matches user's current simulated score range
                          const rangeParts = entry.name.split('-');
                          const min = parseInt(rangeParts[0]);
                          const max = parseInt(rangeParts[1]);
                          const isMatch = currentScore >= min && currentScore <= max;
                          return (
                            <Cell 
                              key={`cell-${idx}`} 
                              fill={isMatch ? bandInfo.color : 'rgba(255,255,255,0.08)'} 
                              style={{ filter: isMatch ? `drop-shadow(0 0 4px ${bandInfo.color}40)` : 'none' }}
                            />
                          );
                        })}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </GlowCard>
            </ScrollReveal>
          </div>

          {/* Action Recommendations */}
          <ScrollReveal direction="up" delay={250}>
            <GlowCard className="dashboard-panel-card" style={{ marginBottom: '24px' }}>
              <div className="panel-header">
                <h3 className="panel-title">Personalized Improvement Actions</h3>
                <span className="panel-badge">Score Gain Tips</span>
              </div>
              <div className="dashboard-action-list">
                {actionItems.length > 0 ? actionItems.map((act, idx) => (
                  <div className="dashboard-action-card glass" key={idx}>
                    <span className="dashboard-action-gain">
                      Est Gain: +{act.estimated_score_gain} Pts
                    </span>
                    <span className="dashboard-action-description">
                      {act.plain_language}
                    </span>
                  </div>
                )) : (
                  <div className="dashboard-action-card glass">
                    <span className="dashboard-action-description">
                      Complete another assessment to generate more personalized recommendations.
                    </span>
                  </div>
                )}
              </div>
            </GlowCard>
          </ScrollReveal>
        </div>
      </main>
    </div>
  );
}
