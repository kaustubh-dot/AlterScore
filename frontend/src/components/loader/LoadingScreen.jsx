import { useEffect, useState } from "react";

function wait(ms) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

const BOOT_LOGS = [
  "INITIALIZING RISK KERNEL CONTROLLERS...",
  "BOOTSTRAPPING SECURE QUANT LAYER...",
  "DECRYPTING MULTIDIMENSIONAL BEHAVIOR MATRICES...",
  "OPTIMIZING ACCELERATED WEBGL BUFFERS...",
  "STABILIZING INTERACTION Lifecycles...",
  "SYNAPSE ROUTE CALIBRATION COMPLETED.",
  "COMPLIANCE BOUNDS CHECK: SECURE.",
  "ALGORITHMIC SCORE MATRICES ENGAGED...",
  "SYNCHRONIZING REALTIME TELEMETRY STREAM..."
];

export default function LoadingScreen({ onComplete }) {
  const [progress, setProgress] = useState(0);
  const [exiting, setExiting] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function run() {
      // Step-based bootstrapping speed
      const steps = [0, 4, 11, 22, 34, 45, 59, 73, 88, 96, 100];
      for (let i = 0; i < steps.length; i++) {
        if (cancelled) return;
        setProgress(steps[i]);
        // Fast organic tick pacing
        await wait(steps[i] < 50 ? 140 : 80);
      }
      
      await wait(300);
      if (cancelled) return;
      setExiting(true);
      
      // Gateway exit delay matching the lens scale zoom transition
      await wait(950);
      if (!cancelled) onComplete?.();
    }

    run();
    return () => {
      cancelled = true;
    };
  }, [onComplete]);

  // Dynamically select current system log and memory address based on progress
  const logIndex = Math.min(Math.floor((progress / 100) * BOOT_LOGS.length), BOOT_LOGS.length - 1);
  const activeLog = BOOT_LOGS[logIndex];
  const memoryAddr = `[0x${(32767 + progress * 243).toString(16).toUpperCase()}]`;

  return (
    <div
      className="loading-screen"
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 10000,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background: "var(--bg-void)",
        opacity: exiting ? 0 : 1,
        transition: "opacity 700ms ease-in-out",
        pointerEvents: exiting ? "none" : "auto",
        overflow: "hidden",
      }}
    >
      {/* Dynamic inline styles for rotating reticle ring */}
      <style dangerouslySetInnerHTML={{__html: `
        @keyframes rotateGoldRing {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        @keyframes pulseReticle {
          0%, 100% { opacity: 0.4; }
          50% { opacity: 0.85; }
        }
      `}} />

      {/* 1. Thin Gold Glowing Edge Border Frame (DonProd Style) */}
      <div
        className="donprod-border"
        style={{
          position: "absolute",
          inset: "clamp(12px, 2.5vw, 24px)",
          border: "1px solid rgba(212, 168, 83, 0.35)",
          boxShadow: "0 0 20px rgba(212, 168, 83, 0.08), inset 0 0 20px rgba(212, 168, 83, 0.08)",
          pointerEvents: "none",
          zIndex: 5,
          opacity: exiting ? 0 : 1,
          transition: "opacity 400ms ease-out",
        }}
      />

      {/* 2. Cyber brutalist corners metadata */}
      <div
        className="loader-meta-corners"
        style={{
          position: "absolute",
          inset: "clamp(24px, 4vw, 42px)",
          fontFamily: "var(--font-mono)",
          fontSize: "0.62rem",
          letterSpacing: "0.15em",
          color: "var(--text-muted)",
          textTransform: "uppercase",
          pointerEvents: "none",
          zIndex: 6,
          opacity: exiting ? 0 : 0.85,
          transition: "opacity 400ms ease-out",
        }}
      >
        {/* Top left metadata */}
        <div style={{ position: "absolute", left: 0, top: 0 }}>
          ALTERSCORE ◆ ENGINE
        </div>
        {/* Top center metadata */}
        <div style={{ position: "absolute", left: "50%", top: 0, transform: "translateX(-50%)" }}>
          SYSTEM BOOTSTRAP
        </div>
        {/* Top right metadata */}
        <div style={{ position: "absolute", right: 0, top: 0 }}>
          ◆ ◆ v0.2.0
        </div>
        {/* Bottom left metadata */}
        <div style={{ position: "absolute", left: 0, bottom: 0 }}>
          BEYOND THE <span style={{ color: "var(--accent-orange)", textShadow: "0 0 10px rgba(232, 113, 58, 0.4)" }}>BUREAU</span>
        </div>
        {/* Bottom right metadata */}
        <div style={{ position: "absolute", right: 0, bottom: 0 }}>
          @ALTERSCORE
        </div>
      </div>

      {/* 3. Center Refraction Portal Lens */}
      <div
        className="lens-portal"
        style={{
          width: "clamp(300px, 38vw, 380px)",
          height: "clamp(300px, 38vw, 380px)",
          borderRadius: "50%",
          border: "1px solid rgba(212, 168, 83, 0.32)",
          position: "relative",
          overflow: "hidden",
          boxShadow: "0 0 90px rgba(0, 0, 0, 0.95), inset 0 0 45px rgba(212, 168, 83, 0.15)",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          zIndex: 4,
          transform: exiting ? "scale(9)" : "scale(1)",
          opacity: exiting ? 0 : 1,
          transition: exiting 
            ? "transform 950ms cubic-bezier(0.85, 0, 0.15, 1), opacity 700ms ease-in" 
            : "transform 400ms ease-out",
        }}
      >
        {/* Background Image refracting inside the lens portal */}
        <div
          style={{
            backgroundImage: "url('/bg-hero.png')",
            backgroundSize: "cover",
            backgroundPosition: "center",
            position: "absolute",
            inset: 0,
            transform: "scale(1.45)",
            filter: "brightness(0.45) contrast(1.2) saturate(1.1)",
            zIndex: 1,
            pointerEvents: "none",
          }}
        />

        {/* Center content container */}
        <div
          style={{
            position: "relative",
            zIndex: 2,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            opacity: exiting ? 0 : 1,
            transition: "opacity 300ms ease-out",
            width: "100%",
            height: "100%",
          }}
        >
          {/* Rotating delicate golden compass outer reticle ring */}
          <div
            style={{
              position: "absolute",
              width: "190px",
              height: "190px",
              borderRadius: "50%",
              border: "1px dashed rgba(212, 168, 83, 0.35)",
              animation: "rotateGoldRing 24s linear infinite",
              pointerEvents: "none",
            }}
          />

          {/* Inner solid thin glow circle */}
          <div
            style={{
              position: "absolute",
              width: "150px",
              height: "150px",
              borderRadius: "50%",
              border: "1px solid rgba(212, 168, 83, 0.12)",
              pointerEvents: "none",
            }}
          />

          {/* Ultra-fine Crosshair Center Reticle */}
          <div style={{ position: "absolute", inset: 0, pointerEvents: "none", opacity: 0.35, animation: "pulseReticle 4s ease-in-out infinite" }}>
            {/* Horizontal line */}
            <div style={{ position: "absolute", top: "50%", left: "calc(50% - 25px)", width: "50px", height: "1px", background: "var(--accent-gold)" }} />
            {/* Vertical line */}
            <div style={{ position: "absolute", left: "50%", top: "calc(50% - 25px)", width: "1px", height: "50px", background: "var(--accent-gold)" }} />
          </div>

          {/* Monospace digital counter percentage */}
          <div
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "3.5rem",
              fontWeight: "300",
              letterSpacing: "-0.04em",
              color: "var(--accent-gold)",
              textShadow: "0 0 25px rgba(212, 168, 83, 0.35)",
              zIndex: 3,
              transform: "translateY(-0.2rem)"
            }}
          >
            {String(progress).padStart(3, "0")}
          </div>

          <div
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: "0.58rem",
              letterSpacing: "0.18em",
              color: "var(--text-primary)",
              opacity: 0.6,
              textTransform: "uppercase",
              zIndex: 3,
              marginTop: "-0.3rem"
            }}
          >
            PERCENT
          </div>

          {/* High-precision scrolling telemetry logs below the reticle */}
          <div
            style={{
              position: "absolute",
              bottom: "2.6rem",
              left: "1rem",
              right: "1rem",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: "0.25rem",
              zIndex: 3,
            }}
          >
            <div
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "0.58rem",
                letterSpacing: "0.08em",
                color: "var(--text-secondary)",
                textTransform: "uppercase",
                textAlign: "center",
                maxWidth: "85%",
                whiteSpace: "nowrap",
                overflow: "hidden",
                textOverflow: "ellipsis",
              }}
            >
              {activeLog}
            </div>
            
            <div
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: "0.52rem",
                letterSpacing: "0.1em",
                color: "var(--accent-gold)",
                opacity: 0.8
              }}
            >
              REG_VAL // {memoryAddr} // STAGE_{logIndex}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
