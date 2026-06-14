import { useState, useEffect, useRef } from 'react';
import { XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, BarChart, Bar, Cell } from 'recharts';
import { Activity, BarChart3, Radio } from 'lucide-react';
import ScrollReveal from '../components/animation/ScrollReveal';
import GlowCard from '../components/ui/GlowCard';
import TextReveal from '../components/animation/TextReveal';
import api from '../lib/api';
import { formatApiError } from '../utils/apiErrors';
import './Dashboard.css';

const ANALYTICS_ENDPOINTS = {
  modelStats: '/model-stats',
  globalImportance: '/global-importance',
  scoreDistribution: '/score-distribution',
  rocData: '/roc-data',
  calibration: '/calibration-curve',
  confusionMatrix: '/confusion-matrix',
  drift: '/drift-report',
};

const TEST_SPLIT = 'test_months_11_12';

// Map a score bucket to its risk-band color, mirroring the borrower band palette.
function bucketFill(scoreMin) {
  if (scoreMin >= 750) return '#10B981';
  if (scoreMin >= 650) return '#34D399';
  if (scoreMin >= 550) return '#FBBF24';
  if (scoreMin >= 450) return '#F97316';
  return '#F43F5E';
}

// Pick the row for the evaluation test split, falling back to the first row.
function pickTestRow(rows) {
  if (!Array.isArray(rows) || rows.length === 0) return null;
  return rows.find((r) => r.split === TEST_SPLIT) || rows[0];
}

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const fetchedRef = useRef(false);

  useEffect(() => {
    if (fetchedRef.current) return;
    fetchedRef.current = true;

    const loadAnalytics = async () => {
      try {
        const keys = Object.keys(ANALYTICS_ENDPOINTS);
        const responses = await Promise.all(
          keys.map((key) => api.get(ANALYTICS_ENDPOINTS[key]))
        );
        const payload = {};
        keys.forEach((key, idx) => {
          payload[key] = responses[idx].data;
        });
        setData(payload);
      } catch (err) {
        console.error('Failed to load analytics:', err);
        setError(formatApiError(err, 'Analytics service unavailable.'));
      } finally {
        setLoading(false);
      }
    };

    loadAnalytics();
  }, []);

  if (loading) {
    return (
      <div className="dashboard-layout">
        <main className="dashboard-content" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
          <div style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>
            <span className="pulse-indicator" style={{ margin: '0 auto 16px' }} />
            <p>Loading live model analytics…</p>
          </div>
        </main>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard-layout">
        <main className="dashboard-content" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '60vh' }}>
          <div className="panel-card" style={{ maxWidth: '520px', textAlign: 'center', borderColor: 'rgba(244, 63, 94, 0.3)' }}>
            <h3 className="panel-title" style={{ color: 'var(--accent-rose)', marginBottom: '12px' }}>Analytics Unavailable</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '13px', lineHeight: 1.6 }}>{error}</p>
          </div>
        </main>
      </div>
    );
  }

  // ---- Transform real backend payloads into chart-ready shapes ----
  const modelStats = Array.isArray(data.modelStats) ? data.modelStats : [];
  const primary = pickTestRow(modelStats);

  const importanceItems = data.globalImportance?.items ?? [];
  const globalImportance = importanceItems.map((item) => ({
    name: item.display_name,
    score: item.mean_abs_shap,
    category: item.category,
  }));

  const histogram = data.scoreDistribution?.score_histogram ?? [];
  const scoreDistribution = histogram.map((bucket) => ({
    name: bucket.label,
    count: bucket.count,
    fill: bucketFill(bucket.score_min),
  }));
  const distributionSummary = data.scoreDistribution?.summary ?? null;

  const rocSeries = pickTestRow(data.rocData);
  const rocCurvePoints = rocSeries?.points ?? [];

  const calibrationSeries = pickTestRow(data.calibration);
  const calibrationPoints = (calibrationSeries?.points ?? []).map((point) => ({
    mean_predicted: point.mean_predicted,
    fraction_positive: point.fraction_positive,
    perfect: point.mean_predicted,
  }));

  const cm = pickTestRow(data.confusionMatrix);

  const drift = data.drift ?? null;
  const driftVerdict = drift?.verdict ? drift.verdict.charAt(0).toUpperCase() + drift.verdict.slice(1) : '—';

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
          <p style={{ opacity: 0.4, marginTop: '2px' }}>{primary?.model_name ?? 'model'}</p>
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
                {primary?.model_name ?? '—'}
              </div>
            </GlowCard>
          </ScrollReveal>

          <ScrollReveal direction="up" delay={150} className="kpi-reveal">
            <GlowCard className="kpi-card">
              <div className="kpi-label">Calibration Gap (ECE)</div>
              <div className="kpi-val">{primary ? primary.expected_calibration_error.toFixed(3) : '—'}</div>
            </GlowCard>
          </ScrollReveal>

          <ScrollReveal direction="up" delay={250} className="kpi-reveal">
            <GlowCard className="kpi-card">
              <div className="kpi-label">Max Feature Drift (PSI)</div>
              <div className="kpi-val" style={{ color: 'var(--accent-emerald)' }}>
                {drift ? `${drift.max_psi.toFixed(3)} (${driftVerdict})` : '—'}
              </div>
            </GlowCard>
          </ScrollReveal>

          <ScrollReveal direction="up" delay={350} className="kpi-reveal">
            <GlowCard className="kpi-card">
              <div className="kpi-label">Test Set AUC</div>
              <div className="kpi-val">{primary ? primary.auc_roc.toFixed(3) : '—'}</div>
            </GlowCard>
          </ScrollReveal>
        </section>

        {/* Model Metrics Table */}
        <ScrollReveal direction="up" delay={100}>
          <section className="panel-card" style={{ marginBottom: '32px' }}>
            <div className="panel-header">
              <h3 className="panel-title">Production Model Metrics</h3>
              <span className="panel-badge">By Evaluation Split</span>
            </div>
            <div className="dashboard-table-wrapper">
              <table className="dashboard-table">
                <thead>
                  <tr>
                    <th>Model Name</th>
                    <th>Split</th>
                    <th>ROC AUC</th>
                    <th>PR AUC</th>
                    <th>KS Stat</th>
                    <th>Brier Score</th>
                    <th>ECE</th>
                  </tr>
                </thead>
                <tbody>
                  {modelStats.map((m, idx) => (
                    <tr key={idx} className={m.split === TEST_SPLIT ? 'highlighted' : ''}>
                      <td style={{ fontWeight: 600 }}>{m.model_name} {m.split === TEST_SPLIT && '✓'}</td>
                      <td>{m.split}</td>
                      <td className="mono">{m.auc_roc.toFixed(3)}</td>
                      <td className="mono">{m.auc_pr.toFixed(3)}</td>
                      <td className="mono">{m.ks_statistic.toFixed(3)}</td>
                      <td className="mono">{m.brier_score.toFixed(3)}</td>
                      <td className="mono" style={{ color: m.expected_calibration_error <= 0.04 ? 'var(--accent-emerald)' : 'var(--text-secondary)' }}>
                        {m.expected_calibration_error.toFixed(3)}
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
                <h3 className="panel-title">ROC Curve</h3>
                <span className="panel-badge">Sensitivity</span>
              </div>
              <div className="chart-container">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={rocCurvePoints}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" />
                    <XAxis dataKey="fpr" type="number" domain={[0, 1]} stroke="var(--text-muted)" fontSize={10} label={{ value: 'False Positive Rate', position: 'insideBottom', offset: -5 }} />
                    <YAxis stroke="var(--text-muted)" fontSize={10} domain={[0, 1]} />
                    <Tooltip contentStyle={{ background: '#0B1221', border: '1px solid var(--bg-border)' }} />
                    <Line type="monotone" dataKey="tpr" stroke="var(--accent-primary)" strokeWidth={2.5} dot={false} name={`${rocSeries?.model_name ?? 'Model'} (AUC ${primary?.auc_roc?.toFixed(2) ?? '—'})`} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </ScrollReveal>

          <ScrollReveal direction="right" delay={200}>
            <div className="panel-card">
              <div className="panel-header">
                <h3 className="panel-title">Population Score Distribution</h3>
                <span className="panel-badge">
                  {distributionSummary ? `Median ${Math.round(distributionSummary.median_score)}` : 'Histogram'}
                </span>
              </div>
              <div className="chart-container">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={scoreDistribution}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" />
                    <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={9} />
                    <YAxis stroke="var(--text-muted)" fontSize={10} />
                    <Tooltip contentStyle={{ background: '#0B1221', border: '1px solid var(--bg-border)' }} />
                    <Bar dataKey="count" radius={[3, 3, 0, 0]}>
                      {scoreDistribution.map((entry, idx) => (
                        <Cell key={`cell-${idx}`} fill={entry.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </ScrollReveal>
        </div>

        {/* Confusion Matrix at the model's operating threshold */}
        {cm && (
          <ScrollReveal direction="up" delay={100}>
            <section className="panel-card" style={{ marginBottom: '32px' }}>
              <div className="panel-header" style={{ borderBottom: '1px solid var(--bg-border)', paddingBottom: '12px' }}>
                <h3 className="panel-title">Confusion Matrix</h3>
                <span className="panel-badge">Operating Threshold p ≥ {cm.threshold.toFixed(2)}</span>
              </div>

              <div className="calibrator-hud" style={{ marginTop: '20px' }}>
                <div className="calibrator-slider-box">
                  <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '16px', lineHeight: 1.6 }}>
                    Measured classification outcomes on the held-out test split at the deployed
                    decision threshold. Higher thresholds reduce false positives (defaults) but
                    defer more borrowers.
                  </p>

                  <div className="calibrator-metrics-row">
                    <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--bg-border)', padding: '10px', borderRadius: '6px', textAlign: 'center' }}>
                      <div style={{ fontSize: '9px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Precision</div>
                      <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-number)', fontFamily: 'var(--font-mono)' }}>
                        {cm.precision.toFixed(3)}
                      </div>
                    </div>
                    <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--bg-border)', padding: '10px', borderRadius: '6px', textAlign: 'center' }}>
                      <div style={{ fontSize: '9px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Recall</div>
                      <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-number)', fontFamily: 'var(--font-mono)' }}>
                        {cm.recall.toFixed(3)}
                      </div>
                    </div>
                    <div style={{ background: 'var(--bg-surface)', border: '1px solid var(--bg-border)', padding: '10px', borderRadius: '6px', textAlign: 'center' }}>
                      <div style={{ fontSize: '9px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>F1 Score</div>
                      <div style={{ fontSize: '16px', fontWeight: 700, color: 'var(--text-number)', fontFamily: 'var(--font-mono)' }}>
                        {cm.f1.toFixed(3)}
                      </div>
                    </div>
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px', textAlign: 'center' }}>
                    Confusion Matrix (N = {cm.tp + cm.fp + cm.fn + cm.tn})
                  </div>
                  <div className="matrix-grid">
                    <div className="matrix-cell">
                      <div className="matrix-num">{cm.tp}</div>
                      <div className="matrix-lbl">True Positive (Approve)</div>
                    </div>
                    <div className="matrix-cell" style={{ borderLeftColor: 'rgba(244, 63, 94, 0.2)' }}>
                      <div className="matrix-num" style={{ color: 'var(--accent-rose)' }}>{cm.fp}</div>
                      <div className="matrix-lbl">False Positive (Default)</div>
                    </div>
                    <div className="matrix-cell" style={{ borderTopColor: 'rgba(251, 191, 36, 0.2)' }}>
                      <div className="matrix-num" style={{ color: 'var(--accent-amber)' }}>{cm.fn}</div>
                      <div className="matrix-lbl">False Negative (Reject)</div>
                    </div>
                    <div className="matrix-cell">
                      <div className="matrix-num">{cm.tn}</div>
                      <div className="matrix-lbl">True Negative (Reject)</div>
                    </div>
                  </div>
                </div>
              </div>
            </section>
          </ScrollReveal>
        )}

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
                <h3 className="panel-title">Calibration Curve</h3>
                <span className="panel-badge">Expected Calibration Gap</span>
              </div>
              <div className="chart-container">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={calibrationPoints}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" />
                    <XAxis dataKey="mean_predicted" type="number" domain={[0, 1]} stroke="var(--text-muted)" fontSize={10} label={{ value: 'Mean Predicted Prob', position: 'insideBottom', offset: -5 }} />
                    <YAxis stroke="var(--text-muted)" fontSize={10} domain={[0, 1]} />
                    <Tooltip contentStyle={{ background: '#0B1221', border: '1px solid var(--bg-border)' }} />
                    <Line type="monotone" dataKey="perfect" stroke="var(--text-muted)" strokeDasharray="5 5" name="Perfect Calibration" dot={false} />
                    <Line type="monotone" dataKey="fraction_positive" stroke="var(--accent-emerald)" strokeWidth={2} name={`Ensemble ECE (${primary ? primary.expected_calibration_error.toFixed(3) : '—'})`} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          </ScrollReveal>
        </div>
      </main>
    </div>
  );
}
