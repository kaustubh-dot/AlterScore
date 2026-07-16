import { lazy, Suspense, useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import Navbar from './components/layout/Navbar';
import Footer from './components/layout/Footer';
import Landing from './pages/Landing';
import Assessment from './pages/Assessment';
import CustomCursor from './components/ui/CustomCursor';
import Preloader from './components/ui/Preloader';
import useLenis from './hooks/useLenis';
import useSound from './hooks/useSound';
import { PageTransitionProvider } from './hooks/PageTransitionContext';
import './styles/global.css';

const Results = lazy(() => import('./pages/Results'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const ResearchLab = lazy(() => import('./pages/ResearchLab'));

function AppContent() {
  const [showPreloader, setShowPreloader] = useState(() => {
    return sessionStorage.getItem('alterscore_preloader_seen') !== 'true';
  });
  const location = useLocation();
  const { initAudio } = useSound();

  // Initialize Lenis smooth scroll
  useLenis();

  // Block scroll on page load during preloader
  useEffect(() => {
    if (showPreloader) {
      document.body.style.overflow = 'hidden';
      document.body.classList.remove('preloader-done');
    } else {
      document.body.style.overflow = '';
      document.body.classList.add('preloader-done');
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [showPreloader]);

  // Resume audio only for users who explicitly enabled sound earlier.
  useEffect(() => {
    const handleFirstInteraction = () => {
      initAudio();
      window.removeEventListener('click', handleFirstInteraction);
      window.removeEventListener('keydown', handleFirstInteraction);
      window.removeEventListener('touchstart', handleFirstInteraction);
    };

    window.addEventListener('click', handleFirstInteraction);
    window.addEventListener('keydown', handleFirstInteraction);
    window.addEventListener('touchstart', handleFirstInteraction);

    return () => {
      window.removeEventListener('click', handleFirstInteraction);
      window.removeEventListener('keydown', handleFirstInteraction);
      window.removeEventListener('touchstart', handleFirstInteraction);
    };
  }, [initAudio]);

  const handlePreloadComplete = () => {
    sessionStorage.setItem('alterscore_preloader_seen', 'true');
    setShowPreloader(false);
    document.body.style.overflow = '';
    document.body.classList.add('preloader-done');
    window.dispatchEvent(new CustomEvent('preloadComplete'));
  };

  const isAssessment = location.pathname === '/assessment';
  const hideGlobalChrome = isAssessment || location.pathname === '/dashboard';
  const showFooter = location.pathname === '/' || location.pathname === '/results';

  return (
    <PageTransitionProvider>
      <div className="app-container">
        {showPreloader && (
          <Preloader onComplete={handlePreloadComplete} />
        )}
        <CustomCursor variant={isAssessment ? 'assessment' : 'default'} />
        
        {/* Dashboard and assessment render their own focused navigation. */}
        {!hideGlobalChrome && <Navbar />}

        <div className="content-wrap">
          <Suspense fallback={null}>
            <Routes>
              <Route path="/" element={<Landing />} />
              <Route path="/assessment" element={<Assessment />} />
              <Route path="/results" element={<Results />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/research" element={<ResearchLab />} />
            </Routes>
          </Suspense>
        </div>

        {showFooter && <Footer />}
      </div>
    </PageTransitionProvider>
  );
}

export default function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}
