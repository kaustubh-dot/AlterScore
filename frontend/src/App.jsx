import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/layout/Navbar';
import Footer from './components/layout/Footer';
import Landing from './pages/Landing';
import Assessment from './pages/Assessment';
import Results from './pages/Results';
import Dashboard from './pages/Dashboard';
import './styles/global.css';

export default function App() {
  return (
    <Router>
      <div className="app-container">
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
