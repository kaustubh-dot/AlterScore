import { useState, lazy, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navbar from './components/layout/Navbar';
import Footer from './components/layout/Footer';
import Landing from './pages/Landing';
import CustomCursor from './components/ui/CustomCursor';
import Preloader from './components/ui/Preloader';
import './styles/global.css';

// Landing is the first paint, so it stays eager. The remaining routes are
// code-split — most importantly the Dashboard, which pulls in the heavy
// recharts library that the borrower flow never needs.
const Assessment = lazy(() => import('./pages/Assessment'));
const Results = lazy(() => import('./pages/Results'));
const Dashboard = lazy(() => import('./pages/Dashboard'));

export default function App() {
  const [showPreloader, setShowPreloader] = useState(true);

  const handlePreloadComplete = () => {
    setShowPreloader(false);
  };

  return (
    <Router>
      <div className="app-container">
        {showPreloader && (
          <Preloader onComplete={handlePreloadComplete} />
        )}
        {/* Custom cursor everywhere except the assessment, which uses the
            native pointer for a calmer, distraction-free input experience. */}
        <Routes>
          <Route path="/assessment" element={null} />
          <Route path="*" element={<CustomCursor />} />
        </Routes>
        {/* Render nav only on non-assessment screens to keep focus */}
        <Routes>
          <Route path="/assessment" element={null} />
          <Route path="*" element={<Navbar />} />
        </Routes>

        <div className="content-wrap">
          <Suspense fallback={null}>
            <Routes>
              <Route path="/" element={<Landing />} />
              <Route path="/assessment" element={<Assessment />} />
              <Route path="/results" element={<Results />} />
              <Route path="/dashboard" element={<Dashboard />} />
            </Routes>
          </Suspense>
        </div>

        <Routes>
          <Route path="/assessment" element={null} />
          <Route path="*" element={<Footer />} />
        </Routes>
      </div>
    </Router>
  );
}
