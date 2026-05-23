import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { PRESET_PROFILES } from "../../data/presets.js";
import { submitScore } from "../../services/api.js";
import { gsap } from "gsap";

export default function DemoDrawer({ isOpen, onClose }) {
  const drawerRef = useRef(null);
  const navigate = useNavigate();
  const [loadingProfile, setLoadingProfile] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen) {
      gsap.to(drawerRef.current, {
        x: 0,
        duration: 0.45,
        ease: "power3.out"
      });
    } else {
      gsap.to(drawerRef.current, {
        x: "100%",
        duration: 0.35,
        ease: "power2.in"
      });
    }
  }, [isOpen]);

  const handleInjectProfile = async (preset) => {
    setLoadingProfile(preset.id);
    setError(null);

    const payload = {
      session_id: `demo-${preset.id}-${Math.random().toString(36).slice(2, 8)}`,
      answers: preset.answers,
      behavioral: preset.behavioral
    };

    try {
      const result = await submitScore(payload);
      // Wait briefly for a smooth transition feel
      await new Promise(resolve => setTimeout(resolve, 800));
      window.sessionStorage.setItem("alterscore_score_result", JSON.stringify(result));
      onClose();
      navigate("/results", { state: result });
    } catch (err) {
      setError(`Model contract rejection: ${err.message || "Engine submission failed"}`);
    } finally {
      setLoadingProfile(null);
    }
  };

  return (
    <>
      {/* Backdrop */}
      {isOpen && (
        <div 
          onClick={onClose}
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            width: "100vw",
            height: "100vh",
            background: "rgba(4, 5, 15, 0.6)",
            backdropFilter: "blur(4px)",
            zIndex: 9999
          }}
        />
      )}

      {/* Slide-out Drawer */}
      <div 
        ref={drawerRef}
        style={{
          position: "fixed",
          top: 0,
          right: 0,
          width: "100%",
          maxWidth: "400px",
          height: "100vh",
          background: "var(--bg-secondary)",
          borderLeft: "1px solid var(--line)",
          boxShadow: "var(--shadow-glass)",
          zIndex: 10000,
          transform: "translateX(100%)",
          display: "flex",
          flexDirection: "column",
          padding: "2rem"
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem" }}>
          <div>
            <div className="mono-text" style={{ fontSize: "0.7rem", color: "var(--accent)" }}>// PRESENTATION PANEL</div>
            <h2 style={{ fontSize: "1.3rem", fontWeight: "700", color: "var(--text-strong)", margin: 0 }}>Preset Profiles</h2>
          </div>
          <button 
            onClick={onClose} 
            style={{ 
              background: "transparent", 
              border: "none", 
              color: "var(--text-muted)", 
              fontSize: "1.2rem", 
              cursor: "pointer",
              padding: "0.2rem 0.5rem" 
            }}
          >
            ✕
          </button>
        </div>

        <p style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginBottom: "2rem", lineHeight: "1.5" }}>
          Inject pre-configured answers and telemetry to demonstrate live scoring variations, SHAP weights, and counterfactual pathways.
        </p>

        {error && (
          <div style={{ padding: "0.8rem", background: "rgba(255,77,94,0.1)", border: "1px solid var(--status-poor)", borderRadius: "4px", fontSize: "0.75rem", color: "var(--status-poor)", marginBottom: "1.5rem" }}>
            {error}
          </div>
        )}

        <div style={{ display: "flex", flexDirection: "column", gap: "1rem", overflowY: "auto", flexGrow: 1, paddingRight: "0.5rem" }}>
          {PRESET_PROFILES.map((preset) => {
            const isLoading = loadingProfile === preset.id;
            return (
              <div 
                key={preset.id}
                style={{
                  border: "1px solid var(--line)",
                  padding: "1rem",
                  borderRadius: "6px",
                  background: "rgba(255,255,255,0.01)",
                  display: "flex",
                  flexDirection: "column",
                  gap: "0.8rem"
                }}
              >
                <div>
                  <strong style={{ fontSize: "0.9rem", color: "var(--text-strong)", display: "block" }}>{preset.name}</strong>
                  <span style={{ fontSize: "0.75rem", color: "var(--soft)" }}>{preset.description}</span>
                </div>

                <button
                  onClick={() => handleInjectProfile(preset)}
                  disabled={!!loadingProfile}
                  className="btn-accent"
                  style={{
                    padding: "0.5rem 0.8rem",
                    fontSize: "0.75rem",
                    border: "none",
                    borderRadius: "4px",
                    background: isLoading ? "var(--soft)" : "var(--accent)",
                    color: "var(--bg)",
                    fontWeight: "bold",
                    cursor: isLoading ? "not-allowed" : "pointer",
                    textAlign: "center"
                  }}
                >
                  {isLoading ? "Running Evaluation..." : "Inject Profile & Evaluate"}
                </button>
              </div>
            );
          })}
        </div>

        <div className="mono-text" style={{ borderTop: "1px solid var(--line)", paddingTop: "1rem", fontSize: "0.65rem", color: "var(--soft)", textAlign: "center" }}>
          ENSEMBLE CONTROL v0.2.0 // LIVE INJECTION
        </div>
      </div>
    </>
  );
}
