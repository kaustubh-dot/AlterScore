import { Link } from "react-router-dom";

export default function Footer() {
  return (
    <footer className="site-footer" data-section>
      <div className="footer-grid">
        <div>
          <strong>AlterScore</strong>
          <p>Premium credit intelligence for borrowers beyond the bureau.</p>
        </div>
        <nav aria-label="Footer">
          <a href="/#manifesto">How it works</a>
          <Link to="/assessment">Assessment</Link>
          <Link to="/dashboard">Dashboard</Link>
        </nav>
        <div className="footer-cta">
          <Link className="pill-button pill-button--primary" to="/assessment" data-magnetic>
            Start your assessment
          </Link>
        </div>
      </div>
      <div className="footer-wordmark" aria-hidden="true">ALTERSCORE</div>
    </footer>
  );
}
