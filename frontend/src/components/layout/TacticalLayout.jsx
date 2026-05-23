import { lazy, Suspense, useEffect, useMemo, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";

import CustomCursor from "../cursor/CustomCursor.jsx";
import LoadingScreen from "../loader/LoadingScreen.jsx";
import Navbar from "../nav/Navbar.jsx";
import GrainOverlay from "../ui/GrainOverlay.jsx";
import DemoDrawer from "../common/DemoDrawer.jsx";
import useLenis from "../../hooks/useLenis.js";
import useMagneticButton from "../../hooks/useMagneticButton.js";
import useSectionObserver from "../../hooks/useSectionObserver.js";

const BackgroundScene = lazy(() => import("../webgl/BackgroundScene.jsx"));

export default function TacticalLayout() {
  const location = useLocation();
  const [loading, setLoading] = useState(true);
  const [demoDrawerOpen, setDemoDrawerOpen] = useState(false);
  const sessionHash = useMemo(() => Math.random().toString(36).slice(2, 10).toUpperCase(), []);
  useLenis();
  useSectionObserver(location.pathname);
  useMagneticButton();

  useEffect(() => {
    const handleMouseMove = (e) => {
      document.documentElement.style.setProperty('--mouse-x', `${e.clientX}px`);
      document.documentElement.style.setProperty('--mouse-y', `${e.clientY}px`);
    };
    window.addEventListener("mousemove", handleMouseMove);
    return () => window.removeEventListener("mousemove", handleMouseMove);
  }, []);

  return (
    <>
      <Suspense fallback={<div className="background-scene" />}>
        <BackgroundScene />
      </Suspense>
      <div className="radial-vignette" />
      <GrainOverlay />
      <CustomCursor />

      {loading && <LoadingScreen onComplete={() => setLoading(false)} />}
      <div className={`site-shell ${loading ? "is-loading" : "is-ready"}`}>
        <Navbar />
        <Outlet />

        <div 
          className="runtime-corner runtime-corner--right" 
          onClick={() => setDemoDrawerOpen(true)}
          style={{ cursor: "pointer", transition: "color 0.2s" }}
        >
          ENSEMBLE RUNTIME v0.2.0
        </div>
        <div className="runtime-corner runtime-corner--left">
          SESSION HASH: {sessionHash} <br/>
          SCORE CONTRACT: LIVE
        </div>
      </div>

      <DemoDrawer isOpen={demoDrawerOpen} onClose={() => setDemoDrawerOpen(false)} />
    </>
  );
}
