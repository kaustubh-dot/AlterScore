import { useState } from "react";

export default function CounterfactualCards({ actions }) {
  const [checkedFeatures, setCheckedFeatures] = useState({});

  const toggleCheck = (feature) => {
    setCheckedFeatures((prev) => ({
      ...prev,
      [feature]: !prev[feature]
    }));
  };

  const simulatedGain = actions
    .filter((action) => checkedFeatures[action.feature])
    .reduce((sum, action) => sum + action.estimated_score_gain, 0);

  return (
    <div className="result-panel">
      <div className="panel-heading" style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "1rem" }}>
        <div>
          <p className="eyebrow">Counterfactual Actions</p>
          <h2>Moves that can lift you</h2>
        </div>
        {simulatedGain > 0 && (
          <div style={{
            background: "rgba(48,242,210,0.15)",
            border: "1px solid var(--accent)",
            color: "var(--accent)",
            padding: "0.4rem 0.8rem",
            borderRadius: "4px",
            fontSize: "0.85rem",
            fontWeight: "bold",
            fontFamily: "var(--font-mono)",
            animation: "pulse-gain 1.5s infinite alternate"
          }}>
            SIMULATED GAIN: +{simulatedGain} PTS
          </div>
        )}
      </div>

      <p style={{ color: "var(--soft)", fontSize: "0.8rem", marginBottom: "1rem", marginTop: "-0.5rem" }}>
        Check the behavioral habits you intend to practice to calculate your simulated rating improvement.
      </p>

      <div className="counterfactual-grid" style={{ display: "flex", flexDirection: "column", gap: "0.8rem" }}>
        {actions.map((action) => {
          const isChecked = !!checkedFeatures[action.feature];
          return (
            <article 
              className={`counter-card ${isChecked ? "is-checked" : ""}`} 
              key={`${action.feature}-${action.estimated_score_gain}`}
              onClick={() => toggleCheck(action.feature)}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "1rem",
                padding: "1rem",
                background: isChecked ? "rgba(48,242,210,0.02)" : "rgba(255,255,255,0.01)",
                border: isChecked ? "1px solid var(--accent)" : "1px solid var(--line)",
                borderRadius: "6px",
                cursor: "pointer",
                transition: "all 0.25s ease"
              }}
            >
              <div 
                style={{ 
                  width: "18px", 
                  height: "18px", 
                  border: isChecked ? "2px solid var(--accent)" : "2px solid var(--soft)",
                  borderRadius: "3px", 
                  display: "flex", 
                  justifyContent: "center", 
                  alignItems: "center",
                  background: isChecked ? "var(--accent)" : "transparent",
                  transition: "all 0.2s"
                }}
              >
                {isChecked && <span style={{ color: "var(--bg)", fontWeight: "bold", fontSize: "0.75rem" }}>✓</span>}
              </div>

              <div style={{ flexGrow: 1 }}>
                <span className="mono-text" style={{ fontSize: "0.7rem", color: isChecked ? "var(--accent)" : "var(--soft)", display: "block" }}>
                  // TARGET BOOSTER: +{action.estimated_score_gain} POINTS
                </span>
                <p style={{ margin: "0.2rem 0 0 0", color: isChecked ? "var(--text-strong)" : "var(--text-muted)", fontSize: "0.85rem", lineHeight: "1.4" }}>
                  {action.plain_language}
                </p>
              </div>
            </article>
          );
        })}
      </div>

      <style>{`
        @keyframes pulse-gain {
          from { transform: scale(1); }
          to { transform: scale(1.05); }
        }
      `}</style>
    </div>
  );
}
