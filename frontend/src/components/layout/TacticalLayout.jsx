import { useMemo, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";

import { VisualExperienceProvider } from "../../context/VisualExperienceContext.jsx";
import CustomCursor from "../cursor/CustomCursor.jsx";
import LoadingScreen from "../loader/LoadingScreen.jsx";
import Navbar from "../nav/Navbar.jsx";
import GrainOverlay from "../ui/GrainOverlay.jsx";
import ExperienceCanvas from "../webgl/ExperienceCanvas.jsx";
import DemoDrawer from "../common/DemoDrawer.jsx";
import useLenis from "../../hooks/useLenis.js";
import useMagneticButton from "../../hooks/useMagneticButton.js";
import useSectionObserver from "../../hooks/useSectionObserver.js";

function TacticalShell() {
  const location = useLocation();
  const [loading, setLoading] = useState(true);
  const [demoDrawerOpen, setDemoDrawerOpen] = useState(false);
  const sessionHash = useMemo(() => Math.random().toString(36).slice(2, 10).toUpperCase(), []);
  useLenis(loading);
  useSectionObserver(location.pathname);
  useMagneticButton();

  return (
    <>
      <ExperienceCanvas />
      <GrainOverlay />
      <CustomCursor />

      {loading && <LoadingScreen onComplete={() => setLoading(false)} />}
      <div className={`site-shell ${loading ? "is-loading" : "is-ready"}`}>
        <Navbar onOpenDemo={() => setDemoDrawerOpen(true)} />
        <Outlet />

        <div className="runtime-corner runtime-corner--left">SESSION // {sessionHash}</div>
      </div>

      <DemoDrawer isOpen={demoDrawerOpen} onClose={() => setDemoDrawerOpen(false)} />
    </>
  );
}

export default function TacticalLayout() {
  return (
    <VisualExperienceProvider>
      <TacticalShell />
    </VisualExperienceProvider>
  );
}
