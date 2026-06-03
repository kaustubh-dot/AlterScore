import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useVisualExperience } from "../../context/VisualExperienceContext.jsx";

export default function CinematicLanding() {
  const { setMode } = useVisualExperience();
  const [sessionId, setSessionId] = useState("");

  // Initialize page mode and generate a unique session ID
  useEffect(() => {
    setMode("landing");
    setSessionId(`AS-${Math.floor(Math.random() * 90000 + 10000)}`);
  }, [setMode]);

  return (
    <main className="cinematic-landing alterscore-landing">
      {/* Anchors for scroll navigation snap boundaries */}
      <div id="origin" className="anchor" data-frame-anchor="0"></div>
      <div id="about" className="anchor" data-frame-anchor="3890"></div>
      <div id="services" className="anchor" data-frame-anchor="7200"></div>
      <div id="usecases" className="anchor" data-frame-anchor="10370"></div>
      <div id="contact" className="anchor" data-frame-anchor="12640"></div>
      <div id="contacts_inner" className="anchor" data-frame-anchor="12767"></div>

      {/* Loading loop elements */}
      <div id="loopLoader" className="alterscore-loader">
        <div className="loader-visual-container">
          <div className="loader-concentric-pulse pulse-1"></div>
          <div className="loader-concentric-pulse pulse-2"></div>
          <div className="loader-concentric-pulse pulse-3"></div>
          <div className="loader-dashed-orbit"></div>
          <div className="loader-core-glow"></div>
        </div>
        <div className="loader-branding">ALTERSCORE</div>
        <div className="loader-progress-bar">
          <div className="loader-progress-fill" style={{ width: "0%" }}></div>
        </div>
      </div>
      <div id="loopLoaderOverlay" className="alterscore-loader is-overlay">
        <div className="loader-visual-container">
          <div className="loader-concentric-pulse pulse-1"></div>
          <div className="loader-concentric-pulse pulse-2"></div>
          <div className="loader-concentric-pulse pulse-3"></div>
          <div className="loader-dashed-orbit"></div>
          <div className="loader-core-glow"></div>
        </div>
        <div className="loader-branding">LOADING CONTENT</div>
      </div>

      {/* Bottom scroll navigation cue */}
      <div id="spaceNavigation" className="scrollToDiscover showAfterLoading">Scroll to discover</div>

      {/* Right vertical hud rail */}
      <div id="clientsLine"></div>

      {/* Section 1: Origin */}
      <div className="lateralMenu scroll-overlay" data-frame-count="1200" data-frame-range="400">
        <ul>
          <li>
            <div className="sceneName">ORIGIN</div>
            <span>Traditional scores miss what matters. Behavior reveals the truth beneath.</span>
          </li>
          <li data-menutarget="origin" className="active"><a href="#origin">AS.ORIGIN</a></li>
        </ul>
      </div>
      <div className="scroll-overlay-text left scroll-pause" data-frame-count="1200" data-frame-range="400" data-autoscroll-duration="7500">
        <h2>THE CREDIT FILE IS NOT THE FULL STORY</h2>
        <p>TRADITIONAL SCORES MISS WHAT MATTERS / BEHAVIOR REVEALS THE TRUTH BENEATH</p>
      </div>

      {/* Section 2: Signal */}
      <div className="lateralMenu scroll-overlay" data-frame-count="3800" data-frame-range="400">
        <ul>
          <li className="prevSection"><a href="#origin">ORIGIN</a></li>
          <li>
            <div className="sceneName">SIGNAL</div>
            <span>Numeracy, resilience, intent, consistency. 27 behavioral signals captured in minutes.</span>
          </li>
          <li data-menutarget="about" className="active"><a href="#about">AS.SIGNAL</a></li>
        </ul>
      </div>
      <div className="scroll-overlay-text right scroll-pause" data-frame-count="3800" data-frame-range="400" data-autoscroll-duration="7500">
        <h2>BEHAVIOR BECOMES MEASURABLE</h2>
        <p>NUMERACY / RESILIENCE / INTENT / CONSISTENCY / 27 BEHAVIORAL SIGNALS CAPTURED IN MINUTES</p>
      </div>

      {/* Section 3: Model */}
      <div className="lateralMenu scroll-overlay" data-frame-count="7200" data-frame-range="400">
        <ul>
          <li className="prevSection"><a href="#about">SIGNAL</a></li>
          <li>
            <div className="sceneName">MODEL</div>
            <span>Stacked, calibrated, explained. Ensemble intelligence distills signal from noise.</span>
          </li>
          <li data-menutarget="services" className="active"><a href="#services">AS.MODEL</a></li>
        </ul>
      </div>
      <div className="scroll-overlay-text left scroll-pause" data-frame-count="7200" data-frame-range="400" data-autoscroll-duration="7500">
        <h2>SIX MODELS. ONE TRANSPARENT VERDICT.</h2>
        <p>STACKED / CALIBRATED / EXPLAINED / ENSEMBLE INTELLIGENCE DISTILLS SIGNAL FROM NOISE</p>
      </div>

      {/* Section 4: Explain */}
      <div className="lateralMenu scroll-overlay" data-frame-count="10370" data-frame-range="400">
        <ul>
          <li className="prevSection"><a href="#services">MODEL</a></li>
          <li>
            <div className="sceneName">EXPLAIN</div>
            <span>Each factor's contribution visualized. Positive drivers bend right — risk bends left.</span>
          </li>
          <li data-menutarget="usecases" className="active"><a href="#usecases">AS.EXPLAIN</a></li>
        </ul>
      </div>
      <div className="scroll-overlay-text right scroll-pause" data-frame-count="10370" data-frame-range="400" data-autoscroll-duration="7500">
        <h2>EVERY SCORE EXPLAINS ITSELF</h2>
        <p>EACH FACTOR'S CONTRIBUTION VISUALIZED / POSITIVE DRIVERS BEND RIGHT — RISK BENDS LEFT</p>
      </div>

      {/* Section 5: Access (Begin Assessment) */}
      <div className="lateralMenu scroll-overlay" data-frame-count="12640" data-frame-range="400">
        <ul>
          <li className="prevSection"><a href="#usecases">EXPLAIN</a></li>
          <li>
            <div className="sceneName">ACCESS</div>
            <span>An alternative credit score for the underserved. Score band 300 – 850.</span>
          </li>
          <li data-menutarget="contact" className="active"><a href="#contact">AS.ACCESS</a></li>
        </ul>
      </div>
      <div className="scroll-overlay-text center scroll-pause" data-frame-count="12640" data-frame-range="400" data-autoscroll-duration="7500">
        <h2>LET THE FULLER PICTURE DECIDE</h2>
        <p>AN ALTERNATIVE CREDIT SCORE FOR THE UNDERSERVED / SCORE BAND 300 – 850</p>
        <div style={{ marginTop: "2rem", pointerEvents: "auto" }}>
          <Link className="signal-cta" to="/assessment">
            <span>Begin assessment</span>
            <i>↗</i>
          </Link>
        </div>
      </div>

      {/* Bottom left session indicator */}
      <div className="session-indicator" aria-hidden="true" style={{ position: "fixed", bottom: "30px", left: "20px", zIndex: 10, color: "white", fontFamily: "Fraktion Mono", fontSize: "12px" }}>
        <span>SESSION // {sessionId}</span>
      </div>
    </main>
  );
}
