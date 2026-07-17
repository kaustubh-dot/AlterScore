import './Footer.css';

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-container container">
        <div className="footer-brand">
          <span className="brand-name">© {new Date().getFullYear()} AlterScore</span>
          <span className="brand-separator" aria-hidden="true">—</span>
          <span className="brand-desc">Synthetic assessment demo</span>
        </div>
      </div>
    </footer>
  );
}
