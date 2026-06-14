import { Shield } from 'lucide-react';
import useSound from '../../hooks/useSound';
import usePageTransition from '../../hooks/usePageTransition';
import './Footer.css';

export default function Footer() {
  const { transitionTo } = usePageTransition();
  const { playClick } = useSound();

  return (
    <footer className="footer">
      <div className="footer-container container">
        <div className="footer-brand">
          <span className="brand-name">© {new Date().getFullYear()} AlterScore</span>
          <span className="brand-separator">•</span>
          <span className="brand-desc">Behavioral Credit Intelligence</span>
        </div>
        <button
          onClick={() => { playClick(); transitionTo('/admin'); }}
          className="footer-link footer-admin-link"
        >
          <Shield size={12} className="admin-icon" />
          <span>Operator Panel</span>
        </button>
      </div>
    </footer>
  );
}
