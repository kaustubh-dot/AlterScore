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
    const handleRouteClick = () => {
      if (window.HideMenu) {
        window.HideMenu();
      }
    };

    return (
      <>
        <a href="#origin" className="showAfterLoading" id="alterscore-logo">
          ALTERSCORE
        </a>

        <div id="menuBtn" className="showAfterLoading">
          <div className="openMenu">MENU</div>
          <div className="closeMenu">CLOSE</div>
        </div>

        <div id="menuPanel" style={{ "--default-bg": "none" }}>
          <ul>
            <li data-menutarget="origin" className="active">
              <div className="panelBg" style={{ backgroundImage: "url(/images/menu_origin.webp)" }}></div>
              <a href="#origin">ORIGIN</a>
            </li>

            <li data-menutarget="about">
              <div className="panelBg" style={{ backgroundImage: "url(/images/menu_about.webp)" }}></div>
              <a href="#about">SIGNAL</a>
            </li>

            <li data-menutarget="services">
              <div className="panelBg" style={{ backgroundImage: "url(/images/menu_services.webp)" }}></div>
              <a href="#services">MODEL</a>
            </li>

            <li data-menutarget="usecases">
              <div className="panelBg" style={{ backgroundImage: "url(/images/menu_usecases.webp)" }}></div>
              <a href="#usecases">EXPLAIN</a>
            </li>

            <li data-menutarget="contacts">
              <div className="panelBg" style={{ backgroundImage: "url(/images/menu_contacts.webp)" }}></div>
              <a href="#contact">ACCESS</a>
            </li>

            {/* Direct React Router links for AlterScore routes */}
            <li>
              <NavLink to="/assessment" id="nav-assessment-link" style={{ background: "black" }} onClick={handleRouteClick}>
                ASSESSMENT
              </NavLink>
            </li>
            <li>
              <NavLink to="/dashboard" id="nav-dashboard-link" style={{ background: "black" }} onClick={handleRouteClick}>
                DASHBOARD
              </NavLink>
            </li>
          </ul>
        </div>
      </>
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


