import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Activity, ShieldAlert, Cpu } from 'lucide-react';
import './Navbar.css';

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const location = useLocation();

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
        <Link to="/" className="navbar-logo">
          <Activity className="logo-icon" size={16} />
          <span className="logo-text">AlterScore</span>
          <span className="logo-tag">v2.0</span>
        </Link>
        <div className="navbar-links">
          {isDashboard ? (
            <Link to="/" className="navbar-link">
              <Cpu size={14} />
              <span>Borrower Flow</span>
            </Link>
          ) : (
            <Link to="/dashboard" className="navbar-link">
              <ShieldAlert size={14} />
              <span>Evaluator Dashboard</span>
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
}
