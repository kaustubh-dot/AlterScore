import React, { useState, useEffect, useRef } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, BarChart, Bar, Legend } from 'recharts';
import { Activity, ShieldCheck, Database, BarChart3, Radio, Sliders, ChevronRight, Terminal as TermIcon } from 'lucide-react';
import ScrollReveal from '../components/animation/ScrollReveal';
import GlowCard from '../components/ui/GlowCard';
import TextReveal from '../components/animation/TextReveal';
import './Dashboard.css';

export default function Dashboard() {
  // Threshold calibration state
  const [threshold, setThreshold] = useState(0.45);
  
  // Rolling API logs
  const [logs, setLogs] = useState([
    { time: '15:20:01', method: 'POST', path: '/api/score', status: 200, score: 712, id: '642f2574-dd5c' },
    { time: '15:20:12', method: 'GET', path: '/api/health', status: 200, label: 'health_ok' },
    { time: '15:20:25', method: 'POST', path: '/api/score', status: 200, score: 580, id: 'dbd54072-bdfe' }
  ]);
  const logTerminalRef = useRef(null);

  // Append new logs in real-time
  useEffect(() => {
    const logInterval = setInterval(() => {
      const now = new Date();
      const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;
      
      const newLog = Math.random() > 0.35 
        ? {
            time: timeStr,
            method: 'POST',
            path: '/api/score',
            status: 200,
            score: Math.floor(400 + Math.random() * 410),
            id: Math.random().toString(36).substring(2, 6) + '-' + Math.random().toString(36).substring(2, 6)
          }
        : {
            time: timeStr,
            method: 'GET',
            path: Math.random() > 0.5 ? '/api/health' : '/api/drift-report',
            status: 200,
            label: Math.random() > 0.5 ? 'health_ok' : 'psi_stable'
          };

      setLogs(prev => {
        const updated = [...prev, newLog];
        return updated.slice(-8); // Limit size
      });
    }, 3500);

    return () => clearInterval(logInterval);
  }, []);

  // Scroll terminal to bottom
  useEffect(() => {
    if (logTerminalRef.current) {
      logTerminalRef.current.scrollTop = logTerminalRef.current.scrollHeight;
    }
  }, [logs]);

  // Model statistics mock data
  const modelStats = [
    { name: 'Stacking Ensemble', type: 'ensemble', auc: 0.81, pr: 0.86, ks: 0.47, brier: 0.14, ece: 0.03, selected: true },
    { name: 'TabNet PyTorch', type: 'neural', auc: 0.79, pr: 0.82, ks: 0.44, brier: 0.15, ece: 0.05 },
    { name: 'XGBoost Baseline', type: 'classical', auc: 0.77, pr: 0.80, ks: 0.41, brier: 0.17, ece: 0.06 },
    { name: 'Logistic Regression', type: 'classical', auc: 0.72, pr: 0.74, ks: 0.35, brier: 0.18, ece: 0.04 }
  ];

  // Global feature importance mock data
  const globalImportance = [
    { name: 'Future Orientation', score: 0.083, category: 'psychometric' },
    { name: 'Cognitive Reflection', score: 0.074, category: 'psychometric' },
    { name: 'Cognitive Consistency', score: 0.065, category: 'telemetry' },
    { name: 'Conscientiousness', score: 0.058, category: 'psychometric' },
    { name: 'Average Response Time', score: 0.032, category: 'telemetry' },
    { name: 'Resilience Index', score: 0.027, category: 'psychometric' }
  ];

  // Score distribution population mock data
  const scoreDistribution = [
    { name: '300-349', count: 36, fill: '#F43F5E' },
    { name: '350-399', count: 85, fill: '#F43F5E' },
    { name: '400-449', count: 124, fill: '#F43F5E' },
    { name: '450-499', count: 180, fill: '#F97316' },
    { name: '500-549', count: 240, fill: '#F97316' },
    { name: '550-599', count: 320, fill: '#FBBF24' },
    { name: '600-649', count: 375, fill: '#FBBF24' },
    { name: '650-699', count: 290, fill: '#34D399' },
    { name: '700-749', count: 210, fill: '#34D399' },
    { name: '750-799', count: 110, fill: '#10B981' },
    { name: '800-850', count: 42, fill: '#10B981' }
  ];

  // ROC Curve overlaid points mock data
  const rocCurvePoints = [
    { fpr: 0.0, Stacking: 0.0, TabNet: 0.0, LogReg: 0.0 },
    { fpr: 0.1, Stacking: 0.45, TabNet: 0.40, LogReg: 0.28 },
    { fpr: 0.2, Stacking: 0.68, TabNet: 0.61, LogReg: 0.45 },
    { fpr: 0.3, Stacking: 0.81, TabNet: 0.74, LogReg: 0.58 },
    { fpr: 0.4, Stacking: 0.88, TabNet: 0.82, LogReg: 0.68 },
    { fpr: 0.5, Stacking: 0.92, TabNet: 0.88, LogReg: 0.77 },
    { fpr: 0.6, Stacking: 0.95, TabNet: 0.92, LogReg: 0.84 },
    { fpr: 0.7, Stacking: 0.97, TabNet: 0.95, LogReg: 0.90 },
    { fpr: 0.8, Stacking: 0.99, TabNet: 0.98, LogReg: 0.95 },
    { fpr: 0.9, Stacking: 1.0, TabNet: 0.99, LogReg: 0.98 },
    { fpr: 1.0, Stacking: 1.0, TabNet: 1.0, LogReg: 1.0 }
  ];

  // Calibration Curve mock points
  const calibrationPoints = [
    { mean_predicted: 0, fraction_positive: 0, perfect: 0 },
    { mean_predicted: 0.2, fraction_positive: 0.22, perfect: 0.2 },
    { mean_predicted: 0.4, fraction_positive: 0.38, perfect: 0.4 },
    { mean_predicted: 0.6, fraction_positive: 0.57, perfect: 0.6 },
    { mean_predicted: 0.8, fraction_positive: 0.83, perfect: 0.8 },
    { mean_predicted: 1.0, fraction_positive: 1.0, perfect: 1.0 }
  ];

  // Threshold calibration logic math
  const totalPositives = 1200;
  const totalNegatives = 600;

  const tprVal = 0.98 * (1 - threshold * threshold);
  const fprVal = 0.85 * Math.pow(1 - threshold, 1.5);

  const tp = Math.round(totalPositives * tprVal);
  const fn = totalPositives - tp;
  const fp = Math.round(totalNegatives * fprVal);
  const tn = totalNegatives - fp;

  const precision = tp / (tp + fp || 1);
  const recall = tprVal;
  const f1 = 2 * ((precision * recall) / (precision + recall || 1));
  const approvalRate = (tp + fp) / 1800;
  const defaultRate = fp / (tp + fp || 1);

  return (
    <div className="dashboard-layout">
      {/* Sidebar Navigation */}
      <aside className="dashboard-sidebar">
        <div className="sidebar-title">
          <Activity size={18} style={{ color: 'var(--accent-cyan)' }} />
          <span>AlterScore HUD</span>
        </div>
        <nav className="sidebar-menu">
          <a href="/" className="sidebar-item">
            <Radio size={16} />
            <span>Borrower Flow</span>
          </a>
          <a href="#" className="sidebar-item active">
            <BarChart3 size={16} />
            <span>Model Analytics</span>
          </a>
        </nav>
        <div className="sidebar-footer">
          <p>VALIRIA CLUB 2025</p>
          <p style={{ opacity: 0.4, marginTop: '2px' }}>v2.0.0-PROD</p>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="dashboard-content">
        <header className="dashboard-header">
          <span className="dashboard-subtitle">Analytical Console</span>
          <h1 className="dashboard-title">
            <TextReveal text="Model Command Center" />
          </h1>
        </header>

        {/* Top Level KPIs */}
        <section className="kpi-row">
          <ScrollReveal direction="up" delay={50} className="kpi-reveal">
            <GlowCard className="kpi-card">
              <div className="kpi-label">Active Classifier</div>
              <div className="kpi-val" style={{ color: 'var(--accent-primary)', fontSize: '15px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Stacking Ensemble
              </div>
            </GlowCard>
          </ScrollReveal>
          
          <ScrollReveal direction="up" delay={150} className="kpi-reveal">
            <GlowCard className="kpi-card">
              <div className="kpi-label">Calibration Gap (ECE)</div>
              <div className="kpi-val">0.034</div>
            </GlowCard>
          </ScrollReveal>

          <ScrollReveal direction="up" delay={250} className="kpi-reveal">
            <GlowCard className="kpi-card">
              <div className="kpi-label">Max Feature Drift (PSI)</div>
              <div className="kpi-val" style={{ color: 'var(--accent-emerald)' }}>0.12 (Stable)</div>
            </GlowCard>
          </ScrollReveal>

          <ScrollReveal direction="up" delay={350} className="kpi-reveal">
            <GlowCard className="kpi-card">
              <div className="kpi-label">Validation Set AUC</div>
              <div className="kpi-val">0.812</div>
            </GlowCard>
          </ScrollReveal>
        </section>

        {/* Model Metrics Table */}
        <ScrollReveal direction="up" delay={100}>
          <section className="panel-card" style={{ marginBottom: '32px' }}>
            <div className="panel-header">
              <h3 className="panel-title">Production Model Leaderboard</h3>
              <span className="panel-badge">Validation Months 11-12</span>
            </div>
            <div className="dashboard-table-wrapper">
              <table className="dashboard-table">
                <thead>
                  <tr>
                    <th>Model Name</th>
                    <th>Type</th>
                    <th>ROC AUC</th>
                    <th>PR AUC</th>
                    <th>KS Stat</th>
                    <th>Brier Score</th>
                    <th>ECE</th>
                  </tr>
                </thead>
                <tbody>
                  {modelStats.map((m, idx) => (
                    <tr key={idx} className={m.selected ? 'highlighted' : ''}>
                      <td style={{ fontWeight: 600 }}>{m.name} {m.selected && '✓'}</td>
                      <td>{m.type}</td>
                      <td className="mono">{m.auc.toFixed(3)}</td>
                      <td className="mono">{m.pr.toFixed(3)}</td>
                      <td className="mono">{m.ks.toFixed(3)}</td>
                      <td className="mono">{m.brier.toFixed(3)}</td>
                      <td className="mono" style={{ color: m.ece <= 0.04 ? 'var(--accent-emerald)' : 'var(--text-secondary)' }}>
                        {m.ece.toFixed(3)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </ScrollReveal>

        {/* Charts: ROC Curve & Score Distribution */}
        <div className="grid-6-6">
          <ScrollReveal direction="left" delay={200}>
            <div className="panel-card">
              <div className="panel-header">
                <h3 className="panel-title">ROC Curves (Overlaid)</h3>
                <span className="panel-badge">Sensitivity</span>
              </div>
              <div className="chart-container">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={rocCurvePoints}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" />
                    <XAxis dataKey="fpr" stroke="var(--text-muted)" fontSize={10} label={{ value: 'False Positive Rate', position: 'insideBottom', offset: -5 }} />
                    <YAxis stroke="var(--text-muted)" fontSize={10} />
                    <Tooltip contentStyle={{ background: '#0B1221', border: '1px solid var(--bg-border)' }} />
                    <Line type="monotone" dataKey="Stacking" stroke="var(--accent-primary)" strokeWidth={2.5} dot={false} name="Ensemble (0.81)" />
                    <Line type="monotone" dataKey="TabNet" stroke="var(--accent-cyan)" strokeWidth={1.5} dot={false} name="TabNet (0.79)" />
                    <Line type="monotone" dataKey="LogReg" stroke="var(--text-muted)" strokeWidth={1} dot={false} name="LogReg (0.72)" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </ScrollReveal>

          <ScrollReveal direction="right" delay={200}>
            <div className="panel-card">
              <div className="panel-header">
                <h3 className="panel-title">Population Score Distribution</h3>
                <span className="panel-badge">Histogram</span>
              </div>
              <div className="chart-container">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={scoreDistribution}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" />
                    <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={9} />
                    <YAxis stroke="var(--text-muted)" fontSize={10} />
                    <Tooltip contentStyle={{ background: '#0B1221', border: '1px solid var(--bg-border)' }} />
                    <Bar dataKey="count" fill="var(--accent-primary)" radius={[3, 3, 0, 0]}>
                      {scoreDistribution.map((entry, idx) => (
                        <Area key={`cell-${idx}`} fill={entry.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </ScrollReveal>
        </div>

        {/* Interactive Threshold Calibration Hud */}
        <ScrollReveal direction="up" delay={100}>
          <section className="panel-card" style={{ marginBottom: '32px' }}>
            <div className="panel-header" style={{ borderBottom: '1px solid var(--bg-border)', paddingBottom: '12px' }}>
              <h3 className="panel-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Sliders size={16} style={{ color: 'var(--accent-cyan)' }} />
                <span>Interactive Decision Threshold Calibrator</span>
              </h3>
              <span className="panel-badge">Underwriting Sim</span>
            </div>

            <div className="calibrator-hud" style={{ marginTop: '20px' }}>
              <div className="calibrator-slider-box">
                <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '16px', lineHeight: 1.6 }}>
                  Slide the threshold probability below. High values reduce false positive defaults but defer more borrowers. Lower values increase approval volume but introduce higher default rates.
                </p>
                
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>
                  <span>Underwrite Threshold</span>
                  <span className="mono" style={{ color: 'var(--accent-cyan)', fontSize: '14px', fontWeight: 700 }}>
                    p ≥ {threshold.toFixed(2)}
                  </span>
                </div>

                <input
                  type="range"
                  min="0.10"
                  max="0.90"
                  step="0.05"
                  value={threshold}
                  onChange={(e) => setThreshold(parseFloat(e.target.value))}
                  className="optimizer-input-range"
                  style={{ width: '100%', marginBottom: '24px' }}
                />

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
                  <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--bg-border)', padding: '10px', borderRadius: '6px', textAlign: 'center' }}>
                    <div style={{ fontSize: '9px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Approval Rate</div>
                    <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-number)', fontFamily: 'var(--font-mono)' }}>
                      {(approvalRate * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--bg-border)', padding: '10px', borderRadius: '6px', textAlign: 'center' }}>
                    <div style={{ fontSize: '9px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Default Rate</div>
                    <div style={{ fontSize: '16px', fontWeight: 700, color: defaultRate > 0.1 ? 'var(--accent-rose)' : 'var(--accent-emerald)', fontFamily: 'var(--font-mono)' }}>
                      {(defaultRate * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--bg-border)', padding: '10px', borderRadius: '6px', textAlign: 'center' }}>
                    <div style={{ fontSize: '9px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>F1 Score</div>
                    <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-number)', fontFamily: 'var(--font-mono)' }}>
                      {f1.toFixed(3)}
                    </div>
                  </div>
                </div>
              </div>

              <div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px', textAlign: 'center' }}>
                  Confusion Matrix (N = 1800)
                </div>
                <div className="matrix-grid">
                  <div className="matrix-cell">
                    <div className="matrix-num">{tp}</div>
                    <div className="matrix-lbl">True Positive (Approve)</div>
                  </div>
                  <div className="matrix-cell" style={{ borderLeftColor: 'rgba(244, 63, 94, 0.2)' }}>
                    <div className="matrix-num" style={{ color: 'var(--accent-rose)' }}>{fp}</div>
                    <div className="matrix-lbl">False Positive (Default)</div>
                  </div>
                  <div className="matrix-cell" style={{ borderTopColor: 'rgba(251, 191, 36, 0.2)' }}>
                    <div className="matrix-num" style={{ color: 'var(--accent-amber)' }}>{fn}</div>
                    <div className="matrix-lbl">False Negative (Reject)</div>
                  </div>
                  <div className="matrix-cell">
                    <div className="matrix-num">{tn}</div>
                    <div className="matrix-lbl">True Negative (Reject)</div>
                  </div>
                </div>
              </div>
            </div>
          </section>
        </ScrollReveal>

        {/* Charts: Calibration Curve & Global Importance */}
        <div className="grid-6-6">
          <ScrollReveal direction="left" delay={200}>
            <div className="panel-card">
              <div className="panel-header">
                <h3 className="panel-title">Global Feature Importance (SHAP)</h3>
                <span className="panel-badge">Top Contributing Features</span>
              </div>
              <div className="chart-container">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={globalImportance} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" />
                    <XAxis type="number" stroke="var(--text-muted)" fontSize={10} />
                    <YAxis dataKey="name" type="category" stroke="var(--text-muted)" fontSize={9} width={120} />
                    <Tooltip contentStyle={{ background: '#0B1221', border: '1px solid var(--bg-border)' }} />
                    <Bar dataKey="score" fill="var(--accent-primary)" radius={[0, 3, 3, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </ScrollReveal>

          <ScrollReveal direction="right" delay={200}>
            <div className="panel-card">
              <div className="panel-header">
                <h3 className="panel-title">Calibration Curves</h3>
                <span className="panel-badge">Expected Calibration Gap</span>
              </div>
              <div className="chart-container">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={calibrationPoints}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" />
                    <XAxis dataKey="mean_predicted" stroke="var(--text-muted)" fontSize={10} label={{ value: 'Mean Predicted Prob', position: 'insideBottom', offset: -5 }} />
                    <YAxis stroke="var(--text-muted)" fontSize={10} />
                    <Tooltip contentStyle={{ background: '#0B1221', border: '1px solid var(--bg-border)' }} />
                    <Line type="monotone" dataKey="perfect" stroke="var(--text-muted)" strokeDasharray="5 5" name="Perfect Calibration" dot={false} />
                    <Line type="monotone" dataKey="fraction_positive" stroke="var(--accent-emerald)" strokeWidth={2} name="Ensemble ECE (0.034)" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </ScrollReveal>
        </div>

        {/* Live System Logging Panel */}
        <ScrollReveal direction="up" delay={300}>
          <section className="panel-card" style={{ border: '1px solid var(--bg-border)' }}>
            <div className="panel-header">
              <h3 className="panel-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <TermIcon size={14} style={{ color: 'var(--accent-cyan)' }} />
                <span>Real-time API Traffic Streamer</span>
              </h3>
              <span className="panel-badge">Signal Node Log</span>
            </div>

            <div className="terminal-screen" ref={logTerminalRef}>
              {logs.map((log, idx) => (
                <div key={idx} className="log-line">
                  <span className="timestamp">[{log.time}] </span>
                  <span className="method">{log.method} </span>
                  <span className="path">{log.path} </span>
                  {log.score !== undefined ? (
                    <>
                      <span className="status-ok">200 OK </span>
                      <span>- session_id: {log.id}... </span>
                      <span>- score: <span className="score-val">{log.score}</span></span>
                    </>
                  ) : (
                    <span className="status-ok">200 OK - {log.label}</span>
                  )}
                </div>
              ))}
            </div>
          </section>
        </ScrollReveal>

      </main>
    </div>
  );
}
