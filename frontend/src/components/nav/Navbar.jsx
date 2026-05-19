import { NavLink } from "react-router-dom";
import GlitchText from "../ui/GlitchText.jsx";


export default function Navbar() {
  return (
    <header className="nav-shell">
      <NavLink to="/" className="nav-wordmark" data-cursor="interactive" aria-label="AlterScore home">
        <GlitchText text="ALTERSCORE" trigger="hover" />
      </NavLink>

      <nav className="nav-links" aria-label="Primary navigation">
        <a href="/#manifesto" data-magnetic>How it works</a>
        <NavLink to="/assessment" data-magnetic>Assessment</NavLink>
        <NavLink to="/results" data-magnetic>Results</NavLink>
        <NavLink className="nav-cta" to="/assessment" data-magnetic>
          Begin <span aria-hidden="true">→</span>
        </NavLink>
      </nav>
    </header>
  );
}
