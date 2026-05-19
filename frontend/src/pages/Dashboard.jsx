import { useEffect, useState } from "react";
import GlitchText from "../components/ui/GlitchText.jsx";
import { fetchHealth } from "../services/api.js";

const panels = [
  "Model performance",
  "Baseline drift",
  "Global feature importance",
  "ROC / PR curves",
  "Calibration curve",
  "Score distribution",
  "Data drift metrics",
  "Fairness & bias audit",
];

export default function Dashboard() {
  const [health, setHealth] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchHealth().then(setHealth).catch(setError);
  }, []);

  return (
    <main className="assessment-page" style={{ maxWidth: '1000px' }}>
      <div className="glow-bg-radial" />

      <div className="hud-panel" style={{ marginBottom: '2rem', minHeight: 'auto' }}>
        <div className="question-topline">
          <span>RISK ENGINE // ANALYST DASHBOARD</span>
          <span style={{ color: health ? 'var(--accent-green)' : 'var(--accent-red)' }}>
            {health ? "SYSTEM SECURE" : (error ? "OFFLINE" : "CONNECTING")}
          </span>
        </div>
        
        <h2><GlitchText text="MODEL GOVERNANCE CENTER" /></h2>
        <p style={{ maxWidth: '600px', lineHeight: '1.6', marginBottom: '2rem', color: 'var(--muted)', fontSize: '0.9rem' }}>
          TRACK F WILL WIRE EACH ANALYTICS PANEL TO ITS OWN ENDPOINT. THE CURRENT BACKEND IS ALREADY SERVING REPORT-BACKED GOVERNANCE DATA FROM THE FROZEN MODEL REPOSITORY.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
          <div style={{ border: '1px solid var(--line)', padding: '1.5rem', background: 'rgba(255,255,255,0.02)', borderRadius: '6px' }}>
            <div className="mono-text" style={{ color: 'var(--muted)', marginBottom: '0.5rem', fontSize: '0.7rem' }}>// RUNTIME ARCHITECTURE</div>
            <strong style={{ fontSize: '1.1rem', color: 'var(--text-strong)' }}>STACKING ENSEMBLE</strong>
          </div>
          <div style={{ border: '1px solid var(--line)', padding: '1.5rem', background: 'rgba(255,255,255,0.02)', borderRadius: '6px' }}>
            <div className="mono-text" style={{ color: 'var(--muted)', marginBottom: '0.5rem', fontSize: '0.7rem' }}>// GOVERNANCE TRACE</div>
            <strong style={{ fontSize: '1.1rem', color: 'var(--text-strong)' }}>MANIFEST BACKED</strong>
          </div>
          <div style={{ border: '1px solid var(--line)', padding: '1.5rem', background: 'rgba(255,255,255,0.02)', borderRadius: '6px' }}>
            <div className="mono-text" style={{ color: 'var(--muted)', marginBottom: '0.5rem', fontSize: '0.7rem' }}>// TELEMETRY ACTIVE</div>
            <strong style={{ fontSize: '1.1rem', color: 'var(--text-strong)' }}>39 BEHAVIORAL VECTORS</strong>
          </div>
        </div>
      </div>

      <div className="dashboard-grid">
        {panels.map((panel, idx) => (
          <div key={panel} className="hud-panel" style={{ minHeight: 'auto', padding: '1.5rem', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div>
              <div className="mono-text" style={{ color: 'var(--accent)', marginBottom: '1rem', fontSize: '0.7rem' }}>// MODULE_{String(idx+1).padStart(2, '0')}</div>
              <h3 style={{ fontSize: '1.1rem', marginBottom: '1rem', color: 'var(--text-strong)' }}>{panel.toUpperCase()}</h3>
            </div>
            <p className="mono-text" style={{ fontSize: '0.75rem', color: 'var(--soft)' }}>
              AWAITING TRACK F DATA SOURCE BINDING.
            </p>
          </div>
        ))}
      </div>
    </main>
  );
}
