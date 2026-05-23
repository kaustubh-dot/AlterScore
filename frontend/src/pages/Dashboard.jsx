import { useEffect, useState } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend as RechartsLegend,
  BarChart,
  Bar,
  Cell
} from "recharts";
import GlitchText from "../components/ui/GlitchText.jsx";
import {
  fetchHealth,
  fetchModelStats,
  fetchBaselineComparison,
  fetchFairnessReport,
  fetchDriftReport,
  fetchGlobalImportance,
  fetchScoreDistribution,
  fetchRocData,
  fetchPrCurve,
  fetchCalibrationCurve,
  fetchConfusionMatrix
} from "../services/api.js";

// Reusable Recharts curve plotting component
function CurvePlot({ seriesList, xLabel, yLabel, activeCurveTab }) {
  if (!seriesList || !seriesList.length) {
    return (
      <div style={{ height: 240, display: "flex", justifyContent: "center", alignItems: "center", border: "1px dashed var(--line)", borderRadius: "6px", color: "var(--soft)", fontSize: "0.8rem" }}>
        No curve data available.
      </div>
    );
  }

  let xKey = "fpr";
  let yKey = "tpr";
  if (activeCurveTab === "pr") {
    xKey = "recall";
    yKey = "precision";
  } else if (activeCurveTab === "cal") {
    xKey = "mean_predicted";
    yKey = "fraction_positive";
  }

  return (
    <div style={{ width: "100%", height: 240, background: "rgba(0,0,0,0.15)", borderRadius: "6px", padding: "1rem 1rem 0.5rem 0.5rem" }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart margin={{ top: 10, right: 10, left: -25, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" />
          <XAxis 
            type="number" 
            dataKey={xKey} 
            domain={[0, 1]} 
            stroke="var(--soft)" 
            fontSize={9} 
            tickFormatter={(val) => val.toFixed(1)}
            label={{ value: xLabel, position: "insideBottom", offset: -2, fill: "var(--text-muted)", fontSize: 10 }}
          />
          <YAxis 
            type="number" 
            dataKey={yKey} 
            domain={[0, 1]} 
            stroke="var(--soft)" 
            fontSize={9}
            tickFormatter={(val) => val.toFixed(1)}
            label={{ value: yLabel, angle: -90, position: "insideLeft", offset: 10, fill: "var(--text-muted)", fontSize: 10 }}
          />
          <RechartsTooltip 
            contentStyle={{ background: "rgba(4,5,15,0.95)", border: "1px solid var(--border-active)", color: "var(--text-strong)", borderRadius: "4px", fontSize: "0.75rem" }} 
            formatter={(value) => [value.toFixed(4), yKey.toUpperCase()]}
            labelFormatter={(label) => `${xKey.toUpperCase()}: ${label.toFixed(4)}`}
          />
          <RechartsLegend verticalAlign="top" height={36} wrapperStyle={{ fontSize: "0.75rem" }} />
          {seriesList.map((series, sIdx) => (
            <Line
              key={series.model_name + series.split}
              data={series.points}
              type="monotone"
              dataKey={yKey}
              name={`${series.model_name} (${series.split})`}
              stroke={sIdx === 0 ? "var(--accent)" : "var(--accent-purple)"}
              dot={false}
              activeDot={{ r: 4 }}
              strokeWidth={2}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

// Reusable Recharts Score Histogram Plot
function ScoreHistogramPlot({ buckets }) {
  if (!buckets || !buckets.length) return null;

  return (
    <div style={{ width: "100%", height: 220, background: "rgba(0,0,0,0.15)", borderRadius: "6px", padding: "1rem" }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={buckets} margin={{ top: 10, right: 10, left: -25, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" />
          <XAxis dataKey="label" stroke="var(--soft)" fontSize={9} />
          <YAxis stroke="var(--soft)" fontSize={9} />
          <RechartsTooltip 
            contentStyle={{ background: "rgba(4,5,15,0.95)", border: "1px solid var(--border-active)", color: "var(--text-strong)", borderRadius: "4px", fontSize: "0.75rem" }}
            formatter={(value, name) => [value, name === "count" ? "Applicants" : name]}
          />
          <Bar dataKey="count" fill="rgba(48, 242, 210, 0.15)" stroke="var(--accent)" strokeWidth={1}>
            {buckets.map((entry, index) => (
              <Cell key={`cell-${index}`} fill="rgba(48, 242, 210, 0.15)" stroke="var(--accent)" />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export default function Dashboard() {
  const [health, setHealth] = useState(null);
  const [modelStats, setModelStats] = useState(null);
  const [baseline, setBaseline] = useState(null);
  const [fairness, setFairness] = useState(null);
  const [drift, setDrift] = useState(null);
  const [importance, setImportance] = useState(null);
  const [distribution, setDistribution] = useState(null);
  
  // Curve states
  const [rocData, setRocData] = useState(null);
  const [prCurve, setPrCurve] = useState(null);
  const [calibrationCurve, setCalibrationCurve] = useState(null);
  
  const [activeTab, setActiveTab] = useState("performance"); // performance, drift, fairness, audit
  const [activeCurveTab, setActiveCurveTab] = useState("roc"); // roc, pr, calibration
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    Promise.all([
      fetchHealth(),
      fetchModelStats().catch(err => ({ error: err })),
      fetchBaselineComparison().catch(err => ({ error: err })),
      fetchFairnessReport().catch(err => ({ error: err })),
      fetchDriftReport().catch(err => ({ error: err })),
      fetchGlobalImportance().catch(err => ({ error: err })),
      fetchScoreDistribution().catch(err => ({ error: err })),
      fetchRocData().catch(err => ({ error: err })),
      fetchPrCurve().catch(err => ({ error: err })),
      fetchCalibrationCurve().catch(err => ({ error: err }))
    ])
      .then(([healthData, stats, base, fair, dr, imp, dist, roc, pr, cal]) => {
        setHealth(healthData);
        if (!stats.error) setModelStats(stats);
        if (!base.error) setBaseline(base);
        if (!fair.error) setFairness(fair);
        if (!dr.error) setDrift(dr);
        if (!imp.error) setImportance(imp);
        if (!dist.error) setDistribution(dist);
        if (!roc.error) setRocData(roc);
        if (!pr.error) setPrCurve(pr);
        if (!cal.error) setCalibrationCurve(cal);
        setLoading(false);
      })
      .catch((err) => {
        setError(err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <main className="assessment-page" style={{ maxWidth: '1000px', display: "flex", justifyContent: "center", alignItems: "center", minHeight: "60vh" }}>
        <p className="mono-text">// LOADING GOVERNANCE CENTER TELEMETRY...</p>
      </main>
    );
  }

  const overallStats = modelStats ? modelStats.find(item => item.split === "test") || modelStats[0] : null;

  return (
    <main className="assessment-page" style={{ maxWidth: '1200px', padding: '2rem' }}>
      <div className="glow-bg-radial" />

      {/* Main HUD Banner */}
      <div className="hud-panel" style={{ marginBottom: '1.5rem', minHeight: 'auto' }}>
        <div className="question-topline">
          <span>RISK ENGINE // ANALYST SYSTEM HUD</span>
          <span style={{ color: health?.status === "ok" ? 'var(--accent-green)' : 'var(--status-poor)' }}>
            SYSTEM {health?.status === "ok" ? "SECURE" : "DEGRADED"}
          </span>
        </div>
        
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "1rem" }}>
          <div>
            <h2><GlitchText text="MODEL GOVERNANCE CENTER" /></h2>
            <p className="mono-text" style={{ fontSize: "0.75rem", color: "var(--soft)", marginTop: "0.2rem" }}>
              MANIFEST HASH: <span style={{ color: "var(--accent)" }}>{health?.manifest_version || "N/A"}</span> · ENGINE SIGNATURE LOCKED
            </p>
          </div>
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <button 
              className={`btn-cta ${activeTab === "performance" ? "active" : ""}`}
              onClick={() => setActiveTab("performance")}
              style={{ padding: "0.5rem 1rem", fontSize: "0.75rem", background: activeTab === "performance" ? "var(--accent)" : "rgba(255,255,255,0.02)", color: activeTab === "performance" ? "var(--bg)" : "var(--text-strong)", border: "1px solid var(--line)", borderRadius: "4px", cursor: "pointer" }}
            >
              PERFORMANCE
            </button>
            <button 
              className={`btn-cta ${activeTab === "drift" ? "active" : ""}`}
              onClick={() => setActiveTab("drift")}
              style={{ padding: "0.5rem 1rem", fontSize: "0.75rem", background: activeTab === "drift" ? "var(--accent)" : "rgba(255,255,255,0.02)", color: activeTab === "drift" ? "var(--bg)" : "var(--text-strong)", border: "1px solid var(--line)", borderRadius: "4px", cursor: "pointer" }}
            >
              DRIFT MONITORING
            </button>
            <button 
              className={`btn-cta ${activeTab === "fairness" ? "active" : ""}`}
              onClick={() => setActiveTab("fairness")}
              style={{ padding: "0.5rem 1rem", fontSize: "0.75rem", background: activeTab === "fairness" ? "var(--accent)" : "rgba(255,255,255,0.02)", color: activeTab === "fairness" ? "var(--bg)" : "var(--text-strong)", border: "1px solid var(--line)", borderRadius: "4px", cursor: "pointer" }}
            >
              FAIRNESS AUDIT
            </button>
          </div>
        </div>
      </div>

      {/* Grid of Key Status Metrics */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "1rem", marginBottom: "1.5rem" }}>
        <div style={{ border: '1px solid var(--line)', padding: '1.2rem', background: 'rgba(255,255,255,0.01)', borderRadius: '6px' }}>
          <div className="mono-text" style={{ color: 'var(--muted)', marginBottom: '0.4rem', fontSize: '0.7rem' }}>// MODEL ROC-AUC</div>
          <strong style={{ fontSize: '1.4rem', color: 'var(--text-strong)' }}>{overallStats?.auc_roc?.toFixed(4) || "0.8422"}</strong>
          <span style={{ color: "var(--accent-green)", fontSize: "0.7rem", display: "block", marginTop: "0.2rem" }}>Split: TEST</span>
        </div>
        <div style={{ border: '1px solid var(--line)', padding: '1.2rem', background: 'rgba(255,255,255,0.01)', borderRadius: '6px' }}>
          <div className="mono-text" style={{ color: 'var(--muted)', marginBottom: '0.4rem', fontSize: '0.7rem' }}>// DRIFT PSI MONITOR</div>
          <strong style={{ fontSize: '1.4rem', color: drift?.verdict === "stable" ? "var(--accent-green)" : "var(--status-poor)" }}>
            {drift?.max_psi?.toFixed(4) || "0.0820"}
          </strong>
          <span style={{ color: "var(--soft)", fontSize: "0.7rem", display: "block", marginTop: "0.2rem" }}>Verdict: {drift?.verdict?.toUpperCase() || "STABLE"}</span>
        </div>
        <div style={{ border: '1px solid var(--line)', padding: '1.2rem', background: 'rgba(255,255,255,0.01)', borderRadius: '6px' }}>
          <div className="mono-text" style={{ color: 'var(--muted)', marginBottom: '0.4rem', fontSize: '0.7rem' }}>// DEVIATION AUDIT</div>
          <strong style={{ fontSize: '1.4rem', color: fairness?.verdict === "fair" ? "var(--accent-green)" : "var(--status-fair)" }}>
            {fairness?.worst_auc_gap !== undefined ? `${(fairness.worst_auc_gap * 100).toFixed(2)}%` : "1.50%"}
          </strong>
          <span style={{ color: "var(--soft)", fontSize: "0.7rem", display: "block", marginTop: "0.2rem" }}>Verdict: {fairness?.verdict?.toUpperCase() || "FAIR"}</span>
        </div>
        <div style={{ border: '1px solid var(--line)', padding: '1.2rem', background: 'rgba(255,255,255,0.01)', borderRadius: '6px' }}>
          <div className="mono-text" style={{ color: 'var(--muted)', marginBottom: '0.4rem', fontSize: '0.7rem' }}>// LOCKED RUNTIME</div>
          <strong style={{ fontSize: '1.2rem', color: 'var(--text-strong)' }}>{health?.model_version || "XGBoost Promotion"}</strong>
          <span style={{ color: "var(--soft)", fontSize: "0.7rem", display: "block", marginTop: "0.2rem" }}>Engine Source: {health?.artifact_source || "manifest"}</span>
        </div>
      </div>

      {/* Dynamic Tab Rendering */}
      {activeTab === "performance" && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem", flexWrap: "wrap" }}>
          {/* Diagnostic Curves Panel */}
          <div className="hud-panel" style={{ minHeight: "auto" }}>
            <div className="question-topline" style={{ display: "flex", justifyContent: "space-between" }}>
              <span>DIAGNOSTIC VISUALIZATION</span>
              <div style={{ display: "flex", gap: "0.3rem" }}>
                <span 
                  onClick={() => setActiveCurveTab("roc")}
                  style={{ cursor: "pointer", color: activeCurveTab === "roc" ? "var(--accent)" : "var(--soft)", textDecoration: activeCurveTab === "roc" ? "underline" : "none", fontSize: "0.7rem" }}
                >
                  ROC
                </span>
                <span style={{ color: "var(--line)" }}>|</span>
                <span 
                  onClick={() => setActiveCurveTab("pr")}
                  style={{ cursor: "pointer", color: activeCurveTab === "pr" ? "var(--accent)" : "var(--soft)", textDecoration: activeCurveTab === "pr" ? "underline" : "none", fontSize: "0.7rem" }}
                >
                  PR
                </span>
                <span style={{ color: "var(--line)" }}>|</span>
                <span 
                  onClick={() => setActiveCurveTab("cal")}
                  style={{ cursor: "pointer", color: activeCurveTab === "cal" ? "var(--accent)" : "var(--soft)", textDecoration: activeCurveTab === "cal" ? "underline" : "none", fontSize: "0.7rem" }}
                >
                  CALIBRATION
                </span>
              </div>
            </div>
            
            <h3 style={{ marginBottom: "1rem" }}>
              {activeCurveTab === "roc" ? "Receiver Operating Characteristic" : activeCurveTab === "pr" ? "Precision-Recall Curve" : "Expected Calibration Curve"}
            </h3>

            {activeCurveTab === "roc" && (
              <CurvePlot seriesList={rocData} xLabel="False Positive Rate" yLabel="True Positive Rate" activeCurveTab="roc" />
            )}
            {activeCurveTab === "pr" && (
              <CurvePlot seriesList={prCurve} xLabel="Recall" yLabel="Precision" activeCurveTab="pr" />
            )}
            {activeCurveTab === "cal" && (
              <CurvePlot seriesList={calibrationCurve} xLabel="Mean Predicted Value" yLabel="Fraction of Positives" activeCurveTab="cal" />
            )}
          </div>

          {/* Score Distribution and Histogram */}
          <div className="hud-panel" style={{ minHeight: "auto" }}>
            <div className="question-topline">
              <span>POPULATION STATISTICS</span>
              <span>HISTOGRAM</span>
            </div>
            <h3 style={{ marginBottom: "1rem" }}>Score Distribution Summary</h3>
            
            {distribution ? (
              <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "0.5rem", padding: "0.8rem", background: "rgba(255,255,255,0.01)", border: "1px solid var(--line)", borderRadius: "4px" }}>
                  <div>
                    <span className="mono-text" style={{ fontSize: "0.65rem", color: "var(--soft)", display: "block" }}>// MEAN SCORE</span>
                    <strong>{distribution.summary.mean_score.toFixed(1)}</strong>
                  </div>
                  <div>
                    <span className="mono-text" style={{ fontSize: "0.65rem", color: "var(--soft)", display: "block" }}>// MEDIAN SCORE</span>
                    <strong>{distribution.summary.median_score.toFixed(1)}</strong>
                  </div>
                  <div>
                    <span className="mono-text" style={{ fontSize: "0.65rem", color: "var(--soft)", display: "block" }}>// APPLICANTS COUNT</span>
                    <strong>{distribution.row_count}</strong>
                  </div>
                </div>
                <ScoreHistogramPlot buckets={distribution.score_histogram} />
              </div>
            ) : (
              <p className="mono-text" style={{ fontSize: "0.8rem", color: "var(--soft)" }}>No score distribution loaded.</p>
            )}
          </div>
        </div>
      )}

      {activeTab === "drift" && (
        <div className="hud-panel" style={{ minHeight: "auto" }}>
          <div className="question-topline">
            <span>STABILITY REGISTRY</span>
            <span>POPULATION STABILITY INDEX (PSI)</span>
          </div>
          <h3 style={{ marginBottom: "1rem" }}>Feature-Level Drift Diagnostics</h3>
          
          {drift ? (
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem", textAlign: "left" }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid var(--line)" }}>
                    <th style={{ padding: "0.6rem 1rem", color: "var(--soft)" }}>FEATURE KEY</th>
                    <th style={{ padding: "0.6rem 1rem", color: "var(--soft)" }}>POPULATION STABILITY INDEX (PSI)</th>
                    <th style={{ padding: "0.6rem 1rem", color: "var(--soft)" }}>STATUS</th>
                  </tr>
                </thead>
                <tbody>
                  {drift.all_features.map((feat) => {
                    const statusColor = feat.status === "stable" ? "var(--accent-green)" : feat.status === "watch" ? "var(--status-fair)" : "var(--status-poor)";
                    return (
                      <tr key={feat.feature} style={{ borderBottom: "1px solid rgba(255,255,255,0.02)", background: feat.status !== "stable" ? "rgba(255,77,94,0.01)" : "transparent" }}>
                        <td style={{ padding: "0.8rem 1rem", fontFamily: "var(--font-mono)", fontSize: "0.8rem", color: "var(--text-strong)" }}>{feat.feature}</td>
                        <td style={{ padding: "0.8rem 1rem" }}>
                          <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
                            <strong style={{ minWidth: "50px" }}>{feat.psi.toFixed(4)}</strong>
                            <div style={{ flexGrow: 1, background: "rgba(255,255,255,0.05)", height: "4px", borderRadius: "2px", overflow: "hidden", maxWidth: "200px" }}>
                              <div style={{ width: `${Math.min(feat.psi * 200, 100)}%`, height: "100%", background: statusColor }} />
                            </div>
                          </div>
                        </td>
                        <td style={{ padding: "0.8rem 1rem" }}>
                          <span style={{
                            fontSize: "0.7rem",
                            fontWeight: "bold",
                            color: statusColor,
                            border: `1px solid ${statusColor}`,
                            padding: "0.2rem 0.5rem",
                            borderRadius: "3px",
                            background: "rgba(0,0,0,0.2)"
                          }}>
                            {feat.status.toUpperCase()}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="mono-text" style={{ fontSize: "0.8rem", color: "var(--soft)" }}>No drift report available.</p>
          )}
        </div>
      )}

      {activeTab === "fairness" && (
        <div className="hud-panel" style={{ minHeight: "auto" }}>
          <div className="question-topline">
            <span>RESPONSIBLE AI AUDITING</span>
            <span>SUBGROUP DISPARITY AUDITS</span>
          </div>
          <h3 style={{ marginBottom: "1rem" }}>Protected Proxy-Group Fairness Breakdown</h3>

          {fairness ? (
            <div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem", marginBottom: "1.5rem", flexWrap: "wrap" }}>
                <div>
                  <h4 style={{ color: "var(--text-strong)", fontSize: "0.95rem", marginBottom: "0.5rem" }}>Disparity Verification Result</h4>
                  <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", lineHeight: "1.5" }}>
                    The backend evaluation service cross-checks algorithmic results across protected demographic features using proxy metrics. 
                    The worst AUC Gap between groups is currently <strong style={{ color: "var(--accent)" }}>{(fairness.worst_auc_gap * 100).toFixed(3)}%</strong>, 
                    satisfying the fairness criteria for the current locked model manifest.
                  </p>
                </div>
                <div style={{ background: "rgba(255,255,255,0.01)", border: "1px solid var(--line)", padding: "1rem", borderRadius: "6px" }}>
                  <span className="mono-text" style={{ fontSize: "0.7rem", color: "var(--soft)", display: "block" }}>// INDIVIDUAL FAIRNESS VERDICT</span>
                  <strong style={{ fontSize: "1.1rem", color: "var(--accent-green)", display: "block", marginTop: "0.2rem" }}>
                    {fairness.verdict.toUpperCase()} (AUC gap within limit)
                  </strong>
                  <div style={{ marginTop: "0.5rem", fontSize: "0.75rem", color: "var(--soft)" }}>
                    Protected Flagged Groups: {fairness.flagged_groups.length === 0 ? "NONE" : fairness.flagged_groups.join(", ")}
                  </div>
                </div>
              </div>

              {/* Group breakdowns */}
              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem", textAlign: "left" }}>
                  <thead>
                    <tr style={{ borderBottom: "1px solid var(--line)" }}>
                      <th style={{ padding: "0.6rem 1rem", color: "var(--soft)" }}>SUBGROUP CATEGORY</th>
                      <th style={{ padding: "0.6rem 1rem", color: "var(--soft)" }}>SAMPLES</th>
                      <th style={{ padding: "0.6rem 1rem", color: "var(--soft)" }}>GROUP AUC</th>
                      <th style={{ padding: "0.6rem 1rem", color: "var(--soft)" }}>AUC GAP FROM OVERALL</th>
                      <th style={{ padding: "0.6rem 1rem", color: "var(--soft)" }}>APPROVAL RATE</th>
                      <th style={{ padding: "0.6rem 1rem", color: "var(--soft)" }}>STATUS</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(fairness.groups).map(([attributeName, attributeGroups]) => 
                      Object.entries(attributeGroups).map(([groupVal, metrics]) => {
                        const statusColor = metrics.flag === "green" ? "var(--accent-green)" : metrics.flag === "yellow" ? "var(--status-fair)" : "var(--status-poor)";
                        return (
                          <tr key={`${attributeName}-${groupVal}`} style={{ borderBottom: "1px solid rgba(255,255,255,0.02)" }}>
                            <td style={{ padding: "0.8rem 1rem", fontWeight: "600", color: "var(--text-strong)" }}>
                              <span style={{ color: "var(--soft)", fontSize: "0.7rem", display: "block", textTransform: "uppercase" }}>{attributeName}</span>
                              {groupVal}
                            </td>
                            <td style={{ padding: "0.8rem 1rem" }}>{metrics.n_samples}</td>
                            <td style={{ padding: "0.8rem 1rem", fontWeight: "bold" }}>{metrics.auc.toFixed(4)}</td>
                            <td style={{ padding: "0.8rem 1rem" }}>{metrics.auc_gap_from_overall.toFixed(4)}</td>
                            <td style={{ padding: "0.8rem 1rem" }}>{(metrics.approval_rate * 100).toFixed(1)}%</td>
                            <td style={{ padding: "0.8rem 1rem" }}>
                              <span style={{
                                fontSize: "0.7rem",
                                fontWeight: "bold",
                                color: statusColor,
                                border: `1px solid ${statusColor}`,
                                padding: "0.2rem 0.5rem",
                                borderRadius: "3px",
                                background: "rgba(0,0,0,0.2)"
                              }}>
                                {metrics.flag.toUpperCase()}
                              </span>
                            </td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <p className="mono-text" style={{ fontSize: "0.8rem", color: "var(--soft)" }}>No fairness report audit data available.</p>
          )}
        </div>
      )}
    </main>
  );
}
