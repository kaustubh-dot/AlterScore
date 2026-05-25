import { Link } from "react-router-dom";

export default function Footer() {
  const currentSessionId = "SESSION // " + Math.random().toString(36).substring(2, 10).toUpperCase();

  return (
    <footer 
      className="site-footer" 
      data-section 
      style={{ 
        position: "relative", 
        zIndex: 5,
        borderTop: "1px solid rgba(212, 168, 83, 0.22)",
        background: "linear-gradient(to bottom, rgba(8, 12, 24, 0.95), rgba(4, 6, 12, 1))",
        backdropFilter: "blur(12px)",
        padding: "8rem clamp(1.5rem, 5vw, 6rem) 6rem",
        overflow: "hidden"
      }}
    >
      {/* Decorative top amber ambient glow bar */}
      <div 
        style={{
          position: "absolute",
          top: 0,
          left: "15%",
          right: "15%",
          height: "1px",
          background: "linear-gradient(90deg, transparent, rgba(212, 168, 83, 0.4), transparent)",
          boxShadow: "0 0 15px rgba(212, 168, 83, 0.6)",
        }}
      />

      <div className="footer-grid" style={{ maxWidth: "1400px", margin: "0 auto" }}>
        
        {/* Left Column: Brand & Coordinates */}
        <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
          <div>
            <strong 
              style={{ 
                fontFamily: "var(--font-display)", 
                fontSize: "1.6rem", 
                color: "var(--text-strong)", 
                display: "block",
                letterSpacing: "0.03em",
                textShadow: "0 2px 8px rgba(0, 0, 0, 0.6)"
              }}
            >
              ALTERSCORE
            </strong>
            <p 
              style={{ 
                color: "var(--text-secondary)", 
                fontSize: "0.95rem", 
                marginTop: "0.8rem", 
                maxWidth: "340px", 
                lineHeight: "1.6",
                textShadow: "0 1px 4px rgba(0, 0, 0, 0.5)"
              }}
            >
              A premium explainable credit interface designed for high-fidelity risk metrics and modern financial judgment.
            </p>
          </div>

          {/* Institutional Metadata Coordinate tag */}
          <div 
            style={{ 
              fontFamily: "var(--font-mono)", 
              fontSize: "0.68rem", 
              letterSpacing: "0.1em", 
              color: "var(--text-muted)",
              lineHeight: "1.6"
            }}
          >
            <div>HQ // 51.5074° N, 0.1278° W</div>
            <div>LONDON, UNITED KINGDOM</div>
            <div style={{ color: "var(--accent-gold)", marginTop: "0.3rem" }}>{currentSessionId}</div>
          </div>
        </div>

        {/* Center Column: Clean Directory Navigation Links */}
        <div style={{ display: "flex", flexDirection: "column", gap: "1.2rem" }}>
          <span 
            style={{ 
              fontFamily: "var(--font-mono)", 
              fontSize: "0.72rem", 
              letterSpacing: "0.15em", 
              color: "var(--text-muted)",
              textTransform: "uppercase"
            }}
          >
            Navigation
          </span>
          <nav aria-label="Footer Navigation" style={{ display: "flex", flexDirection: "column", gap: "0.85rem" }}>
            <a 
              href="/#manifesto" 
              style={{ 
                color: "var(--text-primary)", 
                fontSize: "0.92rem", 
                transition: "color 0.2s, transform 0.2s",
                display: "inline-block",
                textShadow: "0 1px 4px rgba(0,0,0,0.4)"
              }} 
              className="hover-gold"
            >
              ◆ How it works
            </a>
            <Link 
              to="/assessment" 
              style={{ 
                color: "var(--text-primary)", 
                fontSize: "0.92rem", 
                transition: "color 0.2s, transform 0.2s",
                display: "inline-block",
                textShadow: "0 1px 4px rgba(0,0,0,0.4)"
              }} 
              className="hover-gold"
            >
              ◆ Assessment Lab
            </Link>
            <Link 
              to="/dashboard" 
              style={{ 
                color: "var(--text-primary)", 
                fontSize: "0.92rem", 
                transition: "color 0.2s, transform 0.2s",
                display: "inline-block",
                textShadow: "0 1px 4px rgba(0,0,0,0.4)"
              }} 
              className="hover-gold"
            >
              ◆ Analytics Dashboard
            </Link>
          </nav>
        </div>

        {/* Right Column: Premium Action Block CTA */}
        <div 
          style={{ 
            display: "flex", 
            flexDirection: "column", 
            gap: "1.2rem", 
            alignItems: "flex-start",
            justifyContent: "space-between" 
          }}
        >
          <div>
            <span 
              style={{ 
                fontFamily: "var(--font-mono)", 
                fontSize: "0.72rem", 
                letterSpacing: "0.15em", 
                color: "var(--text-muted)",
                textTransform: "uppercase",
                display: "block",
                marginBottom: "0.5rem"
              }}
            >
              Engine Access
            </span>
            <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem", maxWidth: "260px", margin: "0 0 1rem" }}>
              Initialize the explainable metrics engine to grade behavioral assets.
            </p>
          </div>
          
          <Link 
            className="pill-button pill-button--primary" 
            to="/assessment" 
            data-magnetic
            style={{
              padding: "0.9rem 2.2rem",
              background: "var(--accent-gold)",
              color: "#080c18",
              fontWeight: "600",
              boxShadow: "0 4px 20px rgba(212, 168, 83, 0.35)",
              border: "1px solid var(--accent-gold)",
              transition: "transform 0.3s, box-shadow 0.3s"
            }}
          >
            Begin assessment →
          </Link>
        </div>

      </div>

      {/* Elegant, Premium Subtle Metallic Outlined Background Wordmark (DonProd Inspired) */}
      <div 
        className="footer-wordmark" 
        aria-hidden="true" 
        style={{ 
          position: "absolute",
          left: "50%",
          bottom: "-0.5rem",
          transform: "translateX(-50%)",
          fontFamily: "var(--font-display)", 
          fontSize: "clamp(6rem, 16vw, 12rem)",
          fontWeight: "900",
          letterSpacing: "0.12em", 
          color: "transparent",
          WebkitTextStroke: "1px rgba(212, 168, 83, 0.07)",
          textShadow: "0 0 30px rgba(212, 168, 83, 0.015)",
          pointerEvents: "none",
          whiteSpace: "nowrap"
        }}
      >
        ALTERSCORE
      </div>

      {/* Very bottom legal copyright bar */}
      <div 
        style={{
          borderTop: "1px solid rgba(212, 168, 83, 0.1)",
          marginTop: "6rem",
          paddingTop: "2rem",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          fontFamily: "var(--font-mono)",
          fontSize: "0.62rem",
          color: "var(--text-muted)",
          letterSpacing: "0.08em",
          position: "relative",
          zIndex: 6
        }}
      >
        <span>© {new Date().getFullYear()} ALTERSCORE. ALL RIGHTS RESERVED.</span>
        <span>DESIGNED FOR INSTINCTIVE RISK INTELLIGENCE</span>
      </div>

    </footer>
  );
}
