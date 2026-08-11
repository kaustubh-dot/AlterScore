import { lazy, Suspense, useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import Navbar from './components/layout/Navbar';
import Footer from './components/layout/Footer';
import Landing from './pages/Landing';
import Assessment from './pages/Assessment';
import Preloader from './components/ui/Preloader';
import useLenis from './hooks/useLenis';
import useSound from './hooks/useSound';
import { PageTransitionProvider } from './hooks/PageTransitionContext';
import { getSessionStorage, readStorageItem, writeStorageItem } from './lib/safeStorage';
import './styles/global.css';

const Results = lazy(() => import('./pages/Results'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const ResearchLab = lazy(() => import('./pages/ResearchLab'));
const NotFound = lazy(() => import('./pages/NotFound'));

function AppContent() {
  const [showPreloader, setShowPreloader] = useState(() => {
    return readStorageItem(getSessionStorage(), 'alterscore_preloader_seen') !== 'true';
  });
  const location = useLocation();
  const { initAudio } = useSound();

  // Initialize Lenis smooth scroll
  useLenis();

  useEffect(() => {
    if (showPreloader) return undefined;
    const focusHeading = () => {
      const heading = document.querySelector('h1');
      if (!heading) return false;
      heading.setAttribute('tabindex', '-1');
      heading.focus({ preventScroll: true });
      return true;
    };
    const observer = new MutationObserver(() => {
      if (focusHeading()) observer.disconnect();
    });
    if (!focusHeading()) observer.observe(document.querySelector('.content-wrap'), { childList: true, subtree: true });
    return () => observer.disconnect();
  }, [location.pathname, showPreloader]);

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
    writeStorageItem(getSessionStorage(), 'alterscore_preloader_seen', 'true');
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
        <a className="skip-link" href="#main-content">Skip to main content</a>
        
        {/* Dashboard and assessment render their own focused navigation. */}
        {!hideGlobalChrome && <Navbar />}

        <div id="main-content" className="content-wrap" tabIndex={-1}>
          <Suspense fallback={<div className="route-loading" role="status"><span>Loading interface</span></div>}>
            <Routes>
              <Route path="/" element={<Landing />} />
              <Route path="/assessment" element={<Assessment />} />
              <Route path="/results" element={<Results />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/research" element={<ResearchLab />} />
              <Route path="*" element={<NotFound />} />
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
