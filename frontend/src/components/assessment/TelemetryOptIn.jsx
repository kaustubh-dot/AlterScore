import { useEffect, useRef } from "react";
import { gsap } from "gsap";

export default function TelemetryOptIn({ onConsent }) {
  const containerRef = useRef(null);

  useEffect(() => {
    gsap.fromTo(
      containerRef.current,
      { autoAlpha: 0, y: 40, filter: "blur(6px)" },
      { autoAlpha: 1, y: 0, filter: "blur(0px)", duration: 0.6, ease: "power3.out" }
    );
  }, []);

  return (
    <div ref={containerRef} className="telemetry-opt-in hud-panel">
      <div className="question-topline">
        <span>GOVERNED ALTERNATIVE SCORING</span>
        <span style={{ color: "var(--accent-green)" }}>SECURE PORTAL</span>
      </div>

      <h1 className="opt-in-title" style={{ fontSize: "2rem", marginBottom: "1.2rem", fontWeight: "700", letterSpacing: "-0.02em" }}>
        Behavioral Integrity Consent
      </h1>

      <p className="opt-in-intro" style={{ lineHeight: "1.6", color: "var(--text-muted)", marginBottom: "1.5rem" }}>
        AlterScore measures creditworthiness by evaluating cognitive styles, decision-making consistency, and problem-solving resilience. To do this fairly, we capture response rhythms rather than traditional invasive financial histories.
      </p>

      <div className="telemetry-grid" style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "1rem", marginBottom: "2rem" }}>
        <div className="telemetry-item-card" style={{ border: "1px solid var(--line)", padding: "1.2rem", borderRadius: "0px", background: "rgba(255,255,255,0.01)" }}>
          <div className="mono-text" style={{ fontSize: "0.75rem", color: "var(--accent)", marginBottom: "0.4rem" }}>// RESPONSE TIMINGS</div>
          <strong style={{ fontSize: "0.95rem", color: "var(--text-strong)", display: "block", marginBottom: "0.3rem" }}>Deliberation Speed</strong>
          <p style={{ fontSize: "0.8rem", color: "var(--muted)", margin: "0", lineHeight: "1.4" }}>Analyzes decision pace to assess question deliberation and confidence.</p>
        </div>

        <div className="telemetry-item-card" style={{ border: "1px solid var(--line)", padding: "1.2rem", borderRadius: "0px", background: "rgba(255,255,255,0.01)" }}>
          <div className="mono-text" style={{ fontSize: "0.75rem", color: "var(--accent)", marginBottom: "0.4rem" }}>// INTERACTION RHYTHM</div>
          <strong style={{ fontSize: "0.95rem", color: "var(--text-strong)", display: "block", marginBottom: "0.3rem" }}>Scroll & Hover Hesitation</strong>
          <p style={{ fontSize: "0.8rem", color: "var(--muted)", margin: "0", lineHeight: "1.4" }}>Measures scroll adjustments to evaluate answer alignment uncertainty.</p>
        </div>

        <div className="telemetry-item-card" style={{ border: "1px solid var(--line)", padding: "1.2rem", borderRadius: "0px", background: "rgba(255,255,255,0.01)" }}>
          <div className="mono-text" style={{ fontSize: "0.75rem", color: "var(--accent)", marginBottom: "0.4rem" }}>// TEXT ENGAGEMENT</div>
          <strong style={{ fontSize: "0.95rem", color: "var(--text-strong)", display: "block", marginBottom: "0.3rem" }}>Deliberation & Speed Ratio</strong>
          <p style={{ fontSize: "0.8rem", color: "var(--muted)", margin: "0", lineHeight: "1.4" }}>Measures typing velocity (WPM) on open-ended problem solving questions.</p>
        </div>

        <div className="telemetry-item-card" style={{ border: "1px solid var(--line)", padding: "1.2rem", borderRadius: "0px", background: "rgba(255,255,255,0.01)" }}>
          <div className="mono-text" style={{ fontSize: "0.75rem", color: "var(--accent)", marginBottom: "0.4rem" }}>// RECONCILIATION</div>
          <strong style={{ fontSize: "0.95rem", color: "var(--text-strong)", display: "block", marginBottom: "0.3rem" }}>Choice Change Rate</strong>
          <p style={{ fontSize: "0.8rem", color: "var(--muted)", margin: "0", lineHeight: "1.4" }}>Records the frequency of altered selections before final locking.</p>
        </div>
      </div>

      <div className="opt-in-footer" style={{ borderTop: "1px solid var(--line)", paddingTop: "1.5rem", display: "flex", flexWrap: "wrap", justifyContent: "space-between", alignItems: "center", gap: "1.5rem" }}>
        <div style={{ maxWidth: "480px" }}>
          <strong style={{ fontSize: "0.85rem", color: "var(--text-strong)", display: "block", marginBottom: "0.2rem" }}>Strict Data Governance Policy</strong>
          <p style={{ fontSize: "0.75rem", color: "var(--soft)", margin: "0", lineHeight: "1.4" }}>
            We never capture actual keystroke text content (except for the final resilience text response length), do not monitor device locations, and do not sell data to brokers.
          </p>
        </div>
        <button
          type="button"
          onClick={onConsent}
          className="btn-accent"
          style={{
            padding: "0.8rem 1.6rem",
            background: "var(--accent)",
            color: "var(--bg)",
            border: "none",
            borderRadius: "0px",
            fontWeight: "bold",
            cursor: "pointer",
            transition: "transform 0.2s, background-color 0.2s"
          }}
          data-magnetic
        >
          Consent & Begin Assessment
        </button>
      </div>
    </div>
  );
}
