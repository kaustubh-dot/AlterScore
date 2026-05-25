import { useMemo, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";

import LoadingScreen from "../loader/LoadingScreen.jsx";
import Navbar from "../nav/Navbar.jsx";
import GrainOverlay from "../ui/GrainOverlay.jsx";
import BackgroundLayer from "../ui/BackgroundLayer.jsx";
import HeroCanvas from "../webgl/HeroCanvas.jsx";
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
      <BackgroundLayer />
      {/* Pinned 3D ScoreOrb canvas overlay */}
      <HeroCanvas />
      <GrainOverlay />

      {loading && <LoadingScreen onComplete={() => setLoading(false)} />}
      <div className={`site-shell ${loading ? "is-loading" : "is-ready"}`}>
        <Navbar onOpenDemo={() => setDemoDrawerOpen(true)} />
        <Outlet />

        <div className="runtime-corner runtime-corner--left">
          SESSION // {sessionHash}
        </div>
      </div>

      <DemoDrawer isOpen={demoDrawerOpen} onClose={() => setDemoDrawerOpen(false)} />
    </>
  );
}
