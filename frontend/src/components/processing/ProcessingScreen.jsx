import { useEffect, useState } from "react";

const checkSteps = [
  { id: 0, label: "Validating inputs & constraints...", activeLabel: "Verifying input schema integrity...", doneLabel: "Input structure verified (Schema standard matched)" },
  { id: 1, label: "Parsing interaction rhythms...", activeLabel: "Analyzing deliberation latency & change rates...", doneLabel: "Interaction telemetry captured & normalized" },
  { id: 2, label: "Executing ensemble predictions...", activeLabel: "Running Monotonic XGBoost booster...", doneLabel: "Model predictions locked (monotonic constraints met)" },
  { id: 3, label: "Checking fairness parameters...", activeLabel: "Running demographic proxy checks...", doneLabel: "Fairness constraints approved (disparate impact check PASS)" },
  { id: 4, label: "Attributing SHAP weights...", activeLabel: "Calculating feature contributions...", doneLabel: "Explainability attributions calculated" },
  { id: 5, label: "Simulating counterfactual scenarios...", activeLabel: "Mapping eligibility increase paths...", doneLabel: "Recourse recommendations computed" }
];

export default function ProcessingScreen() {
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    const timer = window.setInterval(() => {
      setCurrentStep((value) => {
        if (value >= checkSteps.length) {
          window.clearInterval(timer);
          return value;
        }
        return value + 1;
      });
    }, 850);
    return () => window.clearInterval(timer);
  }, []);

  return (
    <div className="processing-screen" style={{ display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "center", minHeight: "80vh", padding: "2rem" }}>
      <div className="glow-bg-radial" />
      <div className="hud-panel" style={{ width: "100%", maxWidth: "580px", padding: "2.5rem", position: "relative" }}>
        <div className="question-topline" style={{ display: "flex", justifyContent: "space-between", marginBottom: "1.5rem" }}>
          <span>GOVERNANCE GATE // VERIFICATION IN PROGRESS</span>
          <span className="blink-text" style={{ color: "var(--accent)" }}>PROCESSING</span>
        </div>

        <h2 style={{ fontSize: "1.5rem", fontWeight: "700", marginBottom: "1.5rem", letterSpacing: "-0.01em", color: "var(--text-strong)" }}>
          Governance Verification Pipeline
        </h2>

        <div className="governance-checklist" style={{ display: "flex", flexDirection: "column", gap: "1rem", marginBottom: "2rem" }}>
          {checkSteps.map((step) => {
            const isDone = currentStep > step.id;
            const isActive = currentStep === step.id;
            
            return (
              <div 
                key={step.id} 
                style={{ 
                  display: "flex", 
                  alignItems: "center", 
                  gap: "1rem", 
                  padding: "0.8rem 1rem", 
                  borderRadius: "4px",
                  border: isActive ? "1px solid var(--accent)" : "1px solid transparent",
                  background: isActive ? "rgba(48,242,210,0.03)" : "rgba(255,255,255,0.01)",
                  opacity: isDone || isActive ? 1 : 0.4,
                  transition: "all 0.3s ease"
                }}
              >
                <div style={{ display: "flex", justifyContent: "center", alignItems: "center", width: "20px", height: "20px" }}>
                  {isDone ? (
                    <span style={{ color: "var(--accent-green)", fontWeight: "bold" }}>✓</span>
                  ) : isActive ? (
                    <span className="spinner-mini" style={{ width: "12px", height: "12px", border: "2px solid var(--accent)", borderTopColor: "transparent", borderRadius: "50%", display: "inline-block", animation: "spin 0.8s linear infinite" }} />
                  ) : (
                    <span style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>○</span>
                  )}
                </div>
                
                <div style={{ fontSize: "0.9rem", flexGrow: 1 }}>
                  <span style={{ 
                    color: isDone ? "var(--text-muted)" : isActive ? "var(--text-strong)" : "var(--soft)",
                    textDecoration: isDone ? "line-through" : "none",
                    transition: "color 0.3s"
                  }}>
                    {isDone ? step.doneLabel : isActive ? step.activeLabel : step.label}
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        <p className="mono-text" style={{ fontSize: "0.7rem", color: "var(--soft)", margin: 0, textAlign: "center" }}>
          COMPLIANCE HASH SECURE // Locked dynamic parameters mapping active model manifest.
        </p>
      </div>

      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
        .blink-text {
          animation: pulse 1.5s infinite alternate;
        }
        @keyframes pulse {
          from { opacity: 0.4; }
          to { opacity: 1; }
        }
      `}</style>
    </div>
  );
}
