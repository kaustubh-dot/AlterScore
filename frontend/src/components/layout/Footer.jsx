import './Footer.css';

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-container container">
        <div className="footer-brand">
          <span className="brand-name">© {new Date().getFullYear()} AlterScore</span>
        </div>
      </div>
    </footer>
  );
}
