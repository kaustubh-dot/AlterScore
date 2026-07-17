import { useEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';
import Lenis from 'lenis';
import { prefersReducedMotion } from '../lib/motionPreferences';

export default function useLenis() {
  const lenisRef = useRef(null);
  const location = useLocation();

  useEffect(() => {
    // Disable smooth scroll on the assessment page
    if (location.pathname === '/assessment' || prefersReducedMotion()) {
      if (lenisRef.current) {
        lenisRef.current.destroy();
        lenisRef.current = null;
      }
      return;
    }

    // Initialize Lenis
    const lenisInstance = new Lenis({
      duration: 1.2,
      easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
      orientation: 'vertical',
      gestureOrientation: 'vertical',
      smoothWheel: true,
      wheelMultiplier: 1,
      touchMultiplier: 2,
      infinite: false,
    });

    lenisRef.current = lenisInstance;

    // Handle scroll rendering loop
    let rafId;
    function raf(time) {
      lenisInstance.raf(time);
      rafId = requestAnimationFrame(raf);
    }
    rafId = requestAnimationFrame(raf);

    // Scroll to top on route change
    lenisInstance.scrollTo(0, { immediate: true });

    return () => {
      cancelAnimationFrame(rafId);
      lenisInstance.destroy();
      lenisRef.current = null;
    };
  }, [location.pathname]);
}


