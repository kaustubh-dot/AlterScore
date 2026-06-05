import { useState, useEffect } from "react";
import { NavLink } from "react-router-dom";
import { useVisualExperience } from "../../context/VisualExperienceContext.jsx";

export default function Navbar({ onOpenDemo }) {
  const { mode } = useVisualExperience();
  const [open, setOpen] = useState(false);

  // Lock scroll while menu is open
  useEffect(() => {
    if (open) {
      document.body.style.overflow = "hidden";
      document.body.classList.add("menu-open");
    } else {
      document.body.style.overflow = "";
      document.body.classList.remove("menu-open");
    }
    return () => {
      document.body.style.overflow = "";
      document.body.classList.remove("menu-open");
    };
  }, [open]);

  if (mode === "landing") {
    return (
      <header className="sidewave-nav">
        <NavLink to="/" className="sidewave-wordmark" aria-label="AlterScore home" onClick={() => setOpen(false)}>
          ALTERSCORE
        </NavLink>

        <button
          type="button"
          className={`sidewave-menu-toggle ${open ? "is-open" : ""}`}
          onClick={() => setOpen((value) => !value)}
          aria-expanded={open}
          aria-controls="landing-menu"
        >
          <span>MENU</span>
          <i />
          <span>CLOSE</span>
        </button>

        <div id="landing-menu" className={`sidewave-menu-panel ${open ? "is-open" : ""}`}>
          <nav aria-label="Landing menu">
            <a href="#origin" onClick={() => setOpen(false)}>
              <small>01</small>
              <span>Origin</span>
            </a>
            <a href="#signal" onClick={() => setOpen(false)}>
              <small>02</small>
              <span>Signal</span>
            </a>
            <a href="#model" onClick={() => setOpen(false)}>
              <small>03</small>
              <span>Model</span>
            </a>
            <a href="#access" onClick={() => setOpen(false)}>
              <small>04</small>
              <span>Access</span>
            </a>
            <NavLink to="/assessment" onClick={() => setOpen(false)}>
              <small>05</small>
              <span>Assessment</span>
            </NavLink>
            <NavLink to="/dashboard" onClick={() => setOpen(false)}>
              <small>06</small>
              <span>Dashboard</span>
            </NavLink>
          </nav>
        </div>
      </header>
    );
  }

  return (
    <header className="nav-shell">
      <NavLink to="/" className="nav-wordmark" aria-label="AlterScore home" onClick={() => setOpen(false)}>
        ALTERSCORE
      </NavLink>

      <button
        type="button"
        className={`nav-menu-toggle ${open ? "is-open" : ""}`}
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        aria-controls="site-menu"
      >
        <span className="menu-btn-label is-menu">MENU</span>
        <span className="menu-btn-dot" />
        <span className="menu-btn-label is-close">CLOSE</span>
      </button>

      <div id="site-menu" className={`site-menu ${open ? "is-open" : ""}`}>
        <div className="site-menu__wrapper">
          <p className="menu-kicker">Explore AlterScore</p>
          <nav aria-label="Primary navigation">
            <NavLink
              to="/"
              onClick={() => setOpen(false)}
            >
              <small>01</small>
              <span>Signal story</span>
            </NavLink>
            <NavLink
              to="/assessment"
              onClick={() => setOpen(false)}
            >
              <small>02</small>
              <span>Assessment</span>
            </NavLink>
            <NavLink
              to="/dashboard"
              onClick={() => setOpen(false)}
            >
              <small>03</small>
              <span>Evaluator dashboard</span>
            </NavLink>
          </nav>
          
          <button
            type="button"
            className="site-menu__preset"
            onClick={() => {
              setOpen(false);
              onOpenDemo();
            }}
          >
            Open scoring presets
          </button>
          
          <div className="site-menu__footer">
            <div className="footer-col">
              <span className="footer-title">LOCATION</span>
              <span className="footer-val">GLOBAL // ONLINE</span>
            </div>
            <div className="footer-col">
              <span className="footer-title">DEVELOPMENT</span>
              <span className="footer-val">ALTERSCORE LABS</span>
            </div>
            <div className="footer-col">
              <span className="footer-title">LICENSE</span>
              <span className="footer-val">NON-COMMERCIAL RESEARCH</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}

