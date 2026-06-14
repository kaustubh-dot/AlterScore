import { GitBranch, Database } from 'lucide-react';
import { getHealthUrl } from '../../lib/api';
import './Footer.css';

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-container container">
        <div className="footer-brand">
          <span className="brand-name">AlterScore</span>
          <span className="brand-separator">•</span>
          <span className="brand-desc">Behavioral Credit Intelligence</span>
          <span className="brand-separator">•</span>
          <span className="brand-club">Valiria Club 2025</span>
        </div>
        <div className="footer-links">
          <a
            href="https://huggingface.co/spaces/coolbot22/alterscore-backend"
            target="_blank"
            rel="noopener noreferrer"
            className="footer-link"
          >
            <Database size={12} />
            <span>API Docs</span>
          </a>
          <a
            href={getHealthUrl()}
            target="_blank"
            rel="noopener noreferrer"
            className="footer-link"
          >
            <Database size={12} />
            <span>Backend Health</span>
          </a>
          <a
            href="https://github.com/kaustubh-dot/AlterScore"
            target="_blank"
            rel="noopener noreferrer"
            className="footer-link"
          >
            <GitBranch size={12} />
            <span>GitHub</span>
          </a>
        </div>
      </div>
    </footer>
  );
}

