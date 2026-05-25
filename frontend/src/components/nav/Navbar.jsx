import { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import GlitchText from "../ui/GlitchText.jsx";

export default function Navbar({ onOpenDemo }) {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 60);
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  return (
    <header className={`nav-shell ${scrolled ? "nav-scrolled" : ""}`}>
      <NavLink to="/" className="nav-wordmark" data-cursor="interactive" aria-label="AlterScore home">
        <GlitchText text="ALTERSCORE" trigger="hover" />
      </NavLink>

      <nav className="nav-links" aria-label="Primary navigation">
        <a href="/#manifesto" data-magnetic>How it works</a>
        <NavLink to="/assessment" data-magnetic>Assessment</NavLink>
        <NavLink to="/results" data-magnetic>Results</NavLink>
        <button 
          onClick={onOpenDemo} 
          className="nav-demo-link" 
          data-magnetic
          style={{
            background: "none",
            border: "none",
            color: "inherit",
            font: "inherit",
            cursor: "pointer",
            padding: 0,
            transition: "color 0.25s var(--ease-premium)"
          }}
        >
          Presets
        </button>
        <NavLink className="nav-cta" to="/assessment" data-magnetic>
          Begin <span aria-hidden="true">→</span>
        </NavLink>
      </nav>
    </header>
  );
}
