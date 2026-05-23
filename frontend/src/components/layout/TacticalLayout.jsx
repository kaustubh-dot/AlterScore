import { lazy, Suspense, useEffect, useMemo, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";

import LoadingScreen from "../loader/LoadingScreen.jsx";
import Navbar from "../nav/Navbar.jsx";
import GrainOverlay from "../ui/GrainOverlay.jsx";
import DemoDrawer from "../common/DemoDrawer.jsx";
import useLenis from "../../hooks/useLenis.js";
import useMagneticButton from "../../hooks/useMagneticButton.js";
import useSectionObserver from "../../hooks/useSectionObserver.js";


export default function TacticalLayout() {
  const location = useLocation();
  const [loading, setLoading] = useState(true);
  const [demoDrawerOpen, setDemoDrawerOpen] = useState(false);
  const sessionHash = useMemo(() => Math.random().toString(36).slice(2, 10).toUpperCase(), []);
  useLenis();
  useSectionObserver(location.pathname);
  useMagneticButton();


  return (
    <>
      <div className="background-scene" />
      <div className="radial-vignette" />
      <GrainOverlay />

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
