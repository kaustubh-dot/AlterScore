import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { Activity, ShieldCheck, Home, Volume2, VolumeX } from 'lucide-react';
import useSound from '../../hooks/useSound';
import usePageTransition from '../../hooks/usePageTransition';
import './Navbar.css';

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const location = useLocation();
  const { transitionTo } = usePageTransition();
  const { muted, playClick, toggleMuted } = useSound();

  useEffect(() => {
    const handleScroll = () => {
      if (window.scrollY > 20) {
        setScrolled(true);
      } else {
        setScrolled(false);
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const isDashboard = location.pathname === '/dashboard';

  return (
    <nav className={`navbar ${scrolled ? 'navbar-scrolled' : ''}`}>
      <div className="navbar-container container">
        <button
          type="button"
          onClick={() => { playClick(); transitionTo('/'); }}
          className="navbar-logo font-mono btn-logo-action"
          aria-label="Go to AlterScore home"
        >
          <Activity className="logo-icon" size={16} />
          <span className="logo-text">AlterScore</span>
        </button>
        <div className="navbar-links">
          <button
            type="button"
            onClick={() => {
              toggleMuted();
              playClick();
            }}
            className="navbar-icon-button"
            aria-label={muted ? 'Turn sound on' : 'Turn sound off'}
            aria-pressed={!muted}
          >
            {muted ? <VolumeX size={14} /> : <Volume2 size={14} />}
          </button>
          {isDashboard ? (
            <button 
              onClick={() => { playClick(); transitionTo('/'); }}
              className="navbar-link"
              aria-label="Go to home"
            >
              <Home size={14} />
              <span>Home</span>
            </button>
          ) : (
            <button 
              onClick={() => { playClick(); transitionTo('/dashboard'); }}
              className="navbar-link"
              aria-label="Open my dashboard"
            >
              <ShieldCheck size={14} />
              <span>My Dashboard</span>
            </button>
          )}
        </div>
      </div>
    </nav>
  );
}
