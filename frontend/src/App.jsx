import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/layout/Navbar';
import Footer from './components/layout/Footer';
import Landing from './pages/Landing';
import Assessment from './pages/Assessment';
import Results from './pages/Results';
import Dashboard from './pages/Dashboard';
import CustomCursor from './components/ui/CustomCursor';
import Preloader from './components/ui/Preloader';
import './styles/global.css';

export default function App() {
  const [showPreloader, setShowPreloader] = useState(() => {
    // Only run preloader once per session to prevent exhaustion on reload/navigation
    return sessionStorage.getItem('alterscore_session_loaded') !== 'true';
  });

  const handlePreloadComplete = () => {
    sessionStorage.setItem('alterscore_session_loaded', 'true');
    setShowPreloader(false);
  };

  return (
    <Router>
      <div className="app-container">
        {showPreloader && (
          <Preloader onComplete={handlePreloadComplete} />
        )}
        <CustomCursor />
        {/* Render nav only on non-assessment screens to keep focus */}
        <Routes>
          <Route path="/assessment" element={null} />
          <Route path="*" element={<Navbar />} />
        </Routes>

        <div className="content-wrap">
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/assessment" element={<Assessment />} />
            <Route path="/results" element={<Results />} />
            <Route path="/dashboard" element={<Dashboard />} />
          </Routes>
        </div>

        <Routes>
          <Route path="/assessment" element={null} />
          <Route path="*" element={<Footer />} />
        </Routes>
      </div>
    </Router>
  );
}
