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
      <div style={{ height: 240, display: "flex", justifyContent: "center", alignItems: "center", border: "1px dashed var(--line)", borderRadius: "0px", color: "var(--soft)", fontSize: "0.8rem" }}>
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
    <div style={{ width: "100%", height: 240, background: "rgba(0,0,0,0.15)", borderRadius: "0px", padding: "1rem 1rem 0.5rem 0.5rem" }}>
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
            contentStyle={{ background: "rgba(4,5,15,0.95)", border: "1px solid var(--border-active)", color: "var(--text-strong)", borderRadius: "0px", fontSize: "0.75rem" }} 
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
    <div style={{ width: "100%", height: 220, background: "rgba(0,0,0,0.15)", borderRadius: "0px", padding: "1rem" }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={buckets} margin={{ top: 10, right: 10, left: -25, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.03)" />
          <XAxis dataKey="label" stroke="var(--soft)" fontSize={9} />
          <YAxis stroke="var(--soft)" fontSize={9} />
          <RechartsTooltip 
            contentStyle={{ background: "rgba(4,5,15,0.95)", border: "1px solid var(--border-active)", color: "var(--text-strong)", borderRadius: "0px", fontSize: "0.75rem" }}
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

// Panel Boundary Loader/Error wrapper component
function PanelWrapper({ title, loading, error, empty, emptyMessage = "Data unavailable", children }) {
  return (
    <div className="hud-panel" style={{ minHeight: "auto", display: "flex", flexDirection: "column" }}>
      <div className="question-topline" style={{ display: "flex", justifyContent: "space-between" }}>
        <span>{title}</span>
        {error && <span style={{ color: "var(--status-poor)" }}>ENGINE ERROR</span>}
        {loading && <span style={{ color: "var(--accent)" }}>LOADING...</span>}
        {!loading && !error && !empty && <span style={{ color: "var(--accent-green)" }}>ACTIVE SECURE</span>}
      </div>

      {loading ? (
        <div style={{ height: 240, display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", gap: "10px" }}>
          <div className="spinner" style={{ width: "30px", height: "30px", border: "2px solid rgba(255,255,255,0.05)", borderTopColor: "var(--accent)", borderRadius: "50%", animation: "spin 1s linear infinite" }} />
          <p className="mono-text" style={{ fontSize: "0.7rem", color: "var(--soft)" }}>// DECRYPTING ARTIFACT DATA...</p>
        </div>
      ) : error ? (
        <div style={{ height: 240, display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", border: "1px dashed var(--status-poor)", borderRadius: "0px", padding: "1.5rem", textAlign: "center" }}>
          <span style={{ fontSize: "1.5rem", marginBottom: "0.5rem" }}>⚠️</span>
          <p className="mono-text" style={{ fontSize: "0.75rem", color: "var(--status-poor)", fontWeight: "bold" }}>ENDPOINT FAILED</p>
          <p className="mono-text" style={{ fontSize: "0.65rem", color: "var(--soft)", marginTop: "0.4rem" }}>{error.message || "Failed to load telemetry payload"}</p>
        </div>
      ) : empty ? (
        <div style={{ height: 240, display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", border: "1px dashed var(--line)", borderRadius: "0px", color: "var(--soft)", fontSize: "0.8rem" }}>
          {emptyMessage}
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", flexGrow: 1 }}>{children}</div>
      )}
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
  const [confusionMatrix, setConfusionMatrix] = useState(null);
  
  // Curve states
  const [rocData, setRocData] = useState(null);
  const [prCurve, setPrCurve] = useState(null);
  const [calibrationCurve, setCalibrationCurve] = useState(null);
  
  const [activeTab, setActiveTab] = useState("performance"); // performance, drift, fairness
  const [activeCurveTab, setActiveCurveTab] = useState("roc"); // roc, pr, calibration
  
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Individual loading/error tracking
  const [panelStates, setPanelStates] = useState({
    stats: { loading: true, error: null },
    baseline: { loading: true, error: null },
    fairness: { loading: true, error: null },
    drift: { loading: true, error: null },
    importance: { loading: true, error: null },
    distribution: { loading: true, error: null },
    roc: { loading: true, error: null },
    pr: { loading: true, error: null },
    cal: { loading: true, error: null },
    matrix: { loading: true, error: null }
  });

  const updatePanel = (panelKey, loadingState, errorState = null) => {
    setPanelStates(prev => ({
      ...prev,
      [panelKey]: { loading: loadingState, error: errorState }
    }));
  };

  useEffect(() => {
    setLoading(true);
    // Base system setup
    fetchHealth()
      .then(healthData => {
        setHealth(healthData);
        setLoading(false);
      })
      .catch((err) => {
        setError(err);
        setLoading(false);
      });

    // Independent Async Telemetry Panel Queries
    fetchModelStats()
      .then(res => { setModelStats(res); updatePanel("stats", false); })
      .catch(err => updatePanel("stats", false, err));

    fetchBaselineComparison()
      .then(res => { setBaseline(res); updatePanel("baseline", false); })
      .catch(err => updatePanel("baseline", false, err));

    fetchFairnessReport()
      .then(res => { setFairness(res); updatePanel("fairness", false); })
      .catch(err => updatePanel("fairness", false, err));

    fetchDriftReport()
      .then(res => { setDrift(res); updatePanel("drift", false); })
      .catch(err => updatePanel("drift", false, err));

    fetchGlobalImportance()
      .then(res => { setImportance(res); updatePanel("importance", false); })
      .catch(err => updatePanel("importance", false, err));

    fetchScoreDistribution()
      .then(res => { setDistribution(res); updatePanel("distribution", false); })
      .catch(err => updatePanel("distribution", false, err));

    fetchRocData()
      .then(res => { setRocData(res); updatePanel("roc", false); })
      .catch(err => updatePanel("roc", false, err));

    fetchPrCurve()
      .then(res => { setPrCurve(res); updatePanel("pr", false); })
      .catch(err => updatePanel("pr", false, err));

    fetchCalibrationCurve()
      .then(res => { setCalibrationCurve(res); updatePanel("cal", false); })
      .catch(err => updatePanel("cal", false, err));

    fetchConfusionMatrix()
      .then(res => { setConfusionMatrix(res); updatePanel("matrix", false); })
      .catch(err => updatePanel("matrix", false, err));
  }, []);

  if (loading) {
    return (
      <main className="assessment-page" style={{ maxWidth: '1000px', display: "flex", justifyContent: "center", alignItems: "center", minHeight: "60vh" }}>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "12px" }}>
          <div className="spinner" style={{ width: "40px", height: "40px", border: "3px solid rgba(255,255,255,0.05)", borderTopColor: "var(--accent)", borderRadius: "50%", animation: "spin 1s linear infinite" }} />
          <p className="mono-text">// ESTABLISHING CONNECTION TO RISK GATE HUD...</p>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="assessment-page" style={{ maxWidth: '1000px', display: "flex", justifyContent: "center", alignItems: "center", minHeight: "60vh" }}>
        <div style={{ textAlign: "center", border: "1px dashed var(--status-poor)", padding: "2.5rem", borderRadius: "0px", background: "rgba(0,0,0,0.2)" }}>
          <h2 style={{ color: "var(--status-poor)", marginBottom: "1rem" }}>CONNECTION FAILED</h2>
          <p className="mono-text" style={{ fontSize: "0.8rem", color: "var(--soft)", marginBottom: "1.5rem" }}>
            The Evaluator backend service is currently unreachable. Make sure the FastAPI backend is running.
          </p>
          <p className="mono-text" style={{ fontSize: "0.7rem", color: "var(--soft)" }}>
            ERROR DETAILS: {error.message || "Failed to resolve backend API"}
          </p>
        </div>
      </main>
    );
  }

  const activeModelName = health?.manifest_version?.replace(/_v\d+$/, "") || null;
  const overallStats = modelStats
    ? modelStats.find((item) => item.model_name === activeModelName && item.split === "test_months_11_12")
      || modelStats.find((item) => item.split === "test_months_11_12")
      || modelStats[0]
    : null;
  const fairnessStatusLabel = fairness
    ? fairness.verdict === "fair" && fairness.flagged_groups?.length === 0
      ? "FAIR"
      : "REVIEW"
    : "UNKNOWN";

  // Reconcile and calculate confusion matrix data
  const matrixItem = confusionMatrix
    ? confusionMatrix.find((item) => item.model_name === activeModelName && item.split === "test_months_11_12")
      || confusionMatrix.find((item) => item.split === "test_months_11_12")
      || confusionMatrix[0]
    : null;

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
              MANIFEST ID: <span style={{ color: "var(--accent)" }}>{health?.manifest_version || "N/A"}</span> | ENGINE SIGNATURE LOCKED
            </p>
          </div>
          <div style={{ display: "flex", gap: "0.5rem" }}>
            <button 
              className={`btn-cta ${activeTab === "performance" ? "active" : ""}`}
              onClick={() => setActiveTab("performance")}
              style={{ padding: "0.5rem 1rem", fontSize: "0.75rem", background: activeTab === "performance" ? "var(--accent)" : "rgba(255,255,255,0.02)", color: activeTab === "performance" ? "var(--bg)" : "var(--text-strong)", border: "1px solid var(--line)", borderRadius: "0px", cursor: "pointer" }}
            >
              PERFORMANCE
            </button>
            <button 
              className={`btn-cta ${activeTab === "drift" ? "active" : ""}`}
              onClick={() => setActiveTab("drift")}
              style={{ padding: "0.5rem 1rem", fontSize: "0.75rem", background: activeTab === "drift" ? "var(--accent)" : "rgba(255,255,255,0.02)", color: activeTab === "drift" ? "var(--bg)" : "var(--text-strong)", border: "1px solid var(--line)", borderRadius: "0px", cursor: "pointer" }}
            >
              DRIFT MONITORING
            </button>
            <button 
              className={`btn-cta ${activeTab === "fairness" ? "active" : ""}`}
              onClick={() => setActiveTab("fairness")}
              style={{ padding: "0.5rem 1rem", fontSize: "0.75rem", background: activeTab === "fairness" ? "var(--accent)" : "rgba(255,255,255,0.02)", color: activeTab === "fairness" ? "var(--bg)" : "var(--text-strong)", border: "1px solid var(--line)", borderRadius: "0px", cursor: "pointer" }}
            >
              FAIRNESS AUDIT
            </button>
          </div>
        </div>
      </div>

      {/* Grid of Key Status Metrics */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "1rem", marginBottom: "1.5rem" }}>
        <div style={{ border: '1px solid var(--line)', padding: '1.2rem', background: 'rgba(255,255,255,0.01)', borderRadius: "0px" }}>
          <div className="mono-text" style={{ color: 'var(--muted)', marginBottom: '0.4rem', fontSize: '0.7rem' }}>// MODEL ROC-AUC</div>
          <strong style={{ fontSize: '1.4rem', color: 'var(--text-strong)' }}>{overallStats?.auc_roc?.toFixed(4) || "N/A"}</strong>
          <span style={{ color: "var(--accent-green)", fontSize: "0.7rem", display: "block", marginTop: "0.2rem" }}>{overallStats?.model_name || "No model metrics"}</span>
        </div>
        <div style={{ border: '1px solid var(--line)', padding: '1.2rem', background: 'rgba(255,255,255,0.01)', borderRadius: "0px" }}>
          <div className="mono-text" style={{ color: 'var(--muted)', marginBottom: '0.4rem', fontSize: '0.7rem' }}>// DRIFT PSI MONITOR</div>
          <strong style={{ fontSize: '1.4rem', color: drift?.verdict === "stable" ? "var(--accent-green)" : "var(--status-poor)" }}>
            {drift?.max_psi?.toFixed(4) || "N/A"}
          </strong>
          <span style={{ color: "var(--soft)", fontSize: "0.7rem", display: "block", marginTop: "0.2rem" }}>Verdict: {drift?.verdict?.toUpperCase() || "UNKNOWN"}</span>
        </div>
        <div style={{ border: '1px solid var(--line)', padding: '1.2rem', background: 'rgba(255,255,255,0.01)', borderRadius: "0px" }}>
          <div className="mono-text" style={{ color: 'var(--muted)', marginBottom: '0.4rem', fontSize: '0.7rem' }}>// DEVIATION AUDIT</div>
          <strong style={{ fontSize: '1.4rem', color: fairness?.verdict === "fair" ? "var(--accent-green)" : "var(--status-fair)" }}>
            {fairness?.worst_auc_gap !== undefined ? `${(fairness.worst_auc_gap * 100).toFixed(2)}%` : "N/A"}
          </strong>
          <span style={{ color: "var(--soft)", fontSize: "0.7rem", display: "block", marginTop: "0.2rem" }}>Verdict: {fairnessStatusLabel}</span>
        </div>
        <div style={{ border: '1px solid var(--line)', padding: '1.2rem', background: 'rgba(255,255,255,0.01)', borderRadius: "0px" }}>
          <div className="mono-text" style={{ color: 'var(--muted)', marginBottom: '0.4rem', fontSize: '0.7rem' }}>// LOCKED RUNTIME</div>
          <strong style={{ fontSize: '1.2rem', color: 'var(--text-strong)' }}>{activeModelName || health?.manifest_version || "N/A"}</strong>
          <span style={{ color: "var(--soft)", fontSize: "0.7rem", display: "block", marginTop: "0.2rem" }}>Engine Source: {health?.artifact_source || "manifest"}</span>
        </div>
      </div>

      {/* Dynamic Tab Rendering */}
      {activeTab === "performance" && (
        <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
          <div className="dashboard-two-col">
            
            {/* Diagnostic Curves Panel */}
            <PanelWrapper 
              title="DIAGNOSTIC VISUALIZATION" 
              loading={panelStates.roc.loading || panelStates.pr.loading || panelStates.cal.loading}
              error={panelStates.roc.error || panelStates.pr.error || panelStates.cal.error}
              empty={!rocData && !prCurve && !calibrationCurve}
            >
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "1rem" }}>
                <h3 style={{ margin: 0 }}>
                  {activeCurveTab === "roc" ? "Receiver Operating Characteristic" : activeCurveTab === "pr" ? "Precision-Recall Curve" : "Expected Calibration Curve"}
                </h3>
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

              {activeCurveTab === "roc" && (
                <CurvePlot seriesList={rocData} xLabel="False Positive Rate" yLabel="True Positive Rate" activeCurveTab="roc" />
              )}
              {activeCurveTab === "pr" && (
                <CurvePlot seriesList={prCurve} xLabel="Recall" yLabel="Precision" activeCurveTab="pr" />
              )}
              {activeCurveTab === "cal" && (
                <CurvePlot seriesList={calibrationCurve} xLabel="Mean Predicted Value" yLabel="Fraction of Positives" activeCurveTab="cal" />
              )}
            </PanelWrapper>

            {/* Score Distribution and Histogram */}
            <PanelWrapper 
              title="POPULATION STATISTICS // HISTOGRAM" 
              loading={panelStates.distribution.loading}
              error={panelStates.distribution.error}
              empty={!distribution}
            >
              <h3 style={{ marginBottom: "1rem" }}>Score Distribution Summary</h3>
              {distribution && (
                <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "0.5rem", padding: "0.8rem", background: "rgba(255,255,255,0.01)", border: "1px solid var(--line)", borderRadius: "0px" }}>
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
              )}
            </PanelWrapper>
          </div>

          {/* New Interactive Confusion Matrix panel */}
          <PanelWrapper 
            title="PREDICTIVE CONFUSION MATRIX" 
            loading={panelStates.matrix.loading}
            error={panelStates.matrix.error}
            empty={!confusionMatrix}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: "1.2rem", flexWrap: "wrap", gap: "10px" }}>
              <h3 style={{ margin: 0 }}>Decisions Grid & Threshold Analysis</h3>
              <span className="mono-text" style={{ fontSize: "0.75rem", color: "var(--soft)" }}>
                CLASSIFICATION THRESHOLD: <strong style={{ color: "var(--accent)" }}>{matrixItem?.threshold?.toFixed(4) || "0.5000"}</strong>
              </span>
            </div>

            {matrixItem && (
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(290px, 1fr))", gap: "2rem" }}>
                {/* 2x2 Matrix Render */}
                <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                  <div className="confusion-matrix-row" style={{ textAlign: "center", fontWeight: "bold", fontSize: "0.75rem", color: "var(--soft)" }}>
                    <div />
                    <div>PREDICTED DEFAULTER</div>
                    <div>PREDICTED REPAYER</div>
                  </div>

                  <div className="confusion-matrix-row" style={{ alignItems: "stretch" }}>
                    <div style={{ display: "flex", justifyContent: "center", alignItems: "center", fontWeight: "bold", fontSize: "0.75rem", color: "var(--soft)", textTransform: "uppercase", padding: "10px", textAlign: "right" }}>
                      Actual Defaulter
                    </div>
                    <div style={{ background: "rgba(255, 77, 94, 0.05)", border: "1px dashed rgba(255, 77, 94, 0.3)", borderRadius: "0px", padding: "1.2rem", textAlign: "center" }}>
                      <span className="mono-text" style={{ fontSize: "0.6rem", color: "rgba(255,77,94,0.7)", display: "block", marginBottom: "0.3rem" }}>TRUE NEGATIVE (TN)</span>
                      <strong style={{ fontSize: "1.6rem", color: "var(--text-strong)", display: "block" }}>{matrixItem.tn}</strong>
                      <span className="mono-text" style={{ fontSize: "0.7rem", color: "var(--soft)" }}>
                        {((matrixItem.tn / (matrixItem.tn + matrixItem.fp + matrixItem.fn + matrixItem.tp)) * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div style={{ background: "rgba(255, 173, 51, 0.05)", border: "1px dashed rgba(255, 173, 51, 0.3)", borderRadius: "0px", padding: "1.2rem", textAlign: "center" }}>
                      <span className="mono-text" style={{ fontSize: "0.6rem", color: "rgba(255,173,51,0.7)", display: "block", marginBottom: "0.3rem" }}>FALSE POSITIVE (FP)</span>
                      <strong style={{ fontSize: "1.6rem", color: "var(--text-strong)", display: "block" }}>{matrixItem.fp}</strong>
                      <span className="mono-text" style={{ fontSize: "0.7rem", color: "var(--soft)" }}>
                        {((matrixItem.fp / (matrixItem.tn + matrixItem.fp + matrixItem.fn + matrixItem.tp)) * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>

                  <div className="confusion-matrix-row" style={{ alignItems: "stretch" }}>
                    <div style={{ display: "flex", justifyContent: "center", alignItems: "center", fontWeight: "bold", fontSize: "0.75rem", color: "var(--soft)", textTransform: "uppercase", padding: "10px", textAlign: "right" }}>
                      Actual Repayer
                    </div>
                    <div style={{ background: "rgba(255, 173, 51, 0.05)", border: "1px dashed rgba(255, 173, 51, 0.3)", borderRadius: "0px", padding: "1.2rem", textAlign: "center" }}>
                      <span className="mono-text" style={{ fontSize: "0.6rem", color: "rgba(255,173,51,0.7)", display: "block", marginBottom: "0.3rem" }}>FALSE NEGATIVE (FN)</span>
                      <strong style={{ fontSize: "1.6rem", color: "var(--text-strong)", display: "block" }}>{matrixItem.fn}</strong>
                      <span className="mono-text" style={{ fontSize: "0.7rem", color: "var(--soft)" }}>
                        {((matrixItem.fn / (matrixItem.tn + matrixItem.fp + matrixItem.fn + matrixItem.tp)) * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div style={{ background: "rgba(48, 242, 210, 0.05)", border: "1px dashed rgba(48, 242, 210, 0.3)", borderRadius: "0px", padding: "1.2rem", textAlign: "center" }}>
                      <span className="mono-text" style={{ fontSize: "0.6rem", color: "rgba(48,242,210,0.7)", display: "block", marginBottom: "0.3rem" }}>TRUE POSITIVE (TP)</span>
                      <strong style={{ fontSize: "1.6rem", color: "var(--text-strong)", display: "block" }}>{matrixItem.tp}</strong>
                      <span className="mono-text" style={{ fontSize: "0.7rem", color: "var(--soft)" }}>
                        {((matrixItem.tp / (matrixItem.tn + matrixItem.fp + matrixItem.fn + matrixItem.tp)) * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                </div>

                {/* Score Rates Panel */}
                <div style={{ display: "flex", flexDirection: "column", gap: "10px", justifyContent: "center" }}>
                  <div className="dashboard-metrics-subgrid">
                    <div style={{ background: "rgba(255,255,255,0.01)", border: "1px solid var(--line)", padding: "0.8rem", borderRadius: "0px" }}>
                      <span className="mono-text" style={{ fontSize: "0.65rem", color: "var(--soft)", display: "block" }}>// CLASSIFIED ACCURACY</span>
                      <strong style={{ fontSize: "1.2rem", color: "var(--text-strong)" }}>{(matrixItem.accuracy * 100).toFixed(2)}%</strong>
                    </div>
                    <div style={{ background: "rgba(255,255,255,0.01)", border: "1px solid var(--line)", padding: "0.8rem", borderRadius: "0px" }}>
                      <span className="mono-text" style={{ fontSize: "0.65rem", color: "var(--soft)", display: "block" }}>// F1 HARMONIC SCORE</span>
                      <strong style={{ fontSize: "1.2rem", color: "var(--text-strong)" }}>{(matrixItem.f1 * 100).toFixed(2)}%</strong>
                    </div>
                  </div>

                  <div className="dashboard-metrics-subgrid">
                    <div style={{ background: "rgba(255,255,255,0.01)", border: "1px solid var(--line)", padding: "0.8rem", borderRadius: "0px" }}>
                      <span className="mono-text" style={{ fontSize: "0.65rem", color: "var(--soft)", display: "block" }}>// PRECISION RATE</span>
                      <strong style={{ fontSize: "1.2rem", color: "var(--text-strong)" }}>{(matrixItem.precision * 100).toFixed(2)}%</strong>
                    </div>
                    <div style={{ background: "rgba(255,255,255,0.01)", border: "1px solid var(--line)", padding: "0.8rem", borderRadius: "0px" }}>
                      <span className="mono-text" style={{ fontSize: "0.65rem", color: "var(--soft)", display: "block" }}>// SENSITIVITY (RECALL)</span>
                      <strong style={{ fontSize: "1.2rem", color: "var(--text-strong)" }}>{(matrixItem.recall * 100).toFixed(2)}%</strong>
                    </div>
                  </div>

                  <div style={{ background: "rgba(255,255,255,0.01)", border: "1px solid var(--line)", padding: "0.8rem", borderRadius: "0px" }}>
                    <span className="mono-text" style={{ fontSize: "0.65rem", color: "var(--soft)", display: "block" }}>// SPECIFICITY (REJECTION ACCURACY)</span>
                    <strong style={{ fontSize: "1.2rem", color: "var(--text-strong)" }}>{(matrixItem.specificity * 100).toFixed(2)}%</strong>
                  </div>
                </div>
              </div>
            )}
          </PanelWrapper>
        </div>
      )}

      {activeTab === "drift" && (
        <PanelWrapper 
          title="STABILITY REGISTRY // POPULATION STABILITY INDEX (PSI)" 
          loading={panelStates.drift.loading}
          error={panelStates.drift.error}
          empty={!drift}
        >
          <h3 style={{ marginBottom: "1rem" }}>Feature-Level Drift Diagnostics</h3>
          {drift && (
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
                            <div style={{ flexGrow: 1, background: "rgba(255,255,255,0.05)", height: "4px", borderRadius: "0px", overflow: "hidden", maxWidth: "200px" }}>
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
                            borderRadius: "0px",
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
          )}
        </PanelWrapper>
      )}

      {activeTab === "fairness" && (
        <PanelWrapper 
          title="RESPONSIBLE AI AUDITING // SUBGROUP DISPARITY AUDITS" 
          loading={panelStates.fairness.loading}
          error={panelStates.fairness.error}
          empty={!fairness}
        >
          <h3 style={{ marginBottom: "1rem" }}>Protected Proxy-Group Fairness Breakdown</h3>
          {fairness && (
            <div>
              <div className="dashboard-two-col" style={{ marginBottom: "1.5rem" }}>
                <div>
                  <h4 style={{ color: "var(--text-strong)", fontSize: "0.95rem", marginBottom: "0.5rem" }}>Disparity Verification Result</h4>
                  <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", lineHeight: "1.5" }}>
                    The backend evaluation service cross-checks algorithmic results across protected demographic features using proxy metrics.
                    The worst AUC gap between groups is currently <strong style={{ color: "var(--accent)" }}>{(fairness.worst_auc_gap * 100).toFixed(3)}%</strong>;
                    the locked manifest keeps this under active review.
                  </p>
                </div>
                <div style={{ background: "rgba(255,255,255,0.01)", border: "1px solid var(--line)", padding: "1rem", borderRadius: "0px" }}>
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
                                borderRadius: "0px",
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
          )}
        </PanelWrapper>
      )}
    </main>
  );
}
