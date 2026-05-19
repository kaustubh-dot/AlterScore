import { motion } from "framer-motion";
import { Link } from "react-router-dom";

export default function HeroSection() {
  return (
    <section className="hero-section" data-section>
      <div className="hero-content">
        <p className="section-kicker">Alternative credit intelligence</p>
        <h1>
          <span>ALTER</span>
          <span>SCORE</span>
        </h1>
        <motion.p
          className="hero-subtitle"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8, duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
        >
          Credit intelligence beyond the bureau.
        </motion.p>
        <div className="hero-actions">
          <Link className="pill-button pill-button--primary" to="/assessment" data-magnetic>
            Begin assessment
          </Link>
          <a className="pill-button" href="#manifesto" data-magnetic>
            Explore system
          </a>
        </div>
      </div>

      <div className="hero-metrics" aria-label="AlterScore runtime metrics">
        <div>
          <span>Model</span>
          <strong>6-base ensemble</strong>
        </div>
        <div>
          <span>Score</span>
          <strong>300-850</strong>
        </div>
        <div>
          <span>Explainability</span>
          <strong>SHAP + DICE</strong>
        </div>
      </div>

      <div className="scroll-indicator">
        <span>Scroll to explore</span>
        <i />
      </div>
    </section>
  );
}
