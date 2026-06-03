import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { useLocation } from "react-router-dom";

import useVisualQuality from "../hooks/useVisualQuality.js";

const VisualExperienceContext = createContext(null);

function getRouteMode(pathname) {
  if (pathname.startsWith("/dashboard")) return "dashboard";
  if (pathname.startsWith("/results")) return "results";
  if (pathname.startsWith("/assessment")) return "assessment";
  return "landing";
}

export function VisualExperienceProvider({ children }) {
  const location = useLocation();
  const qualityTier = useVisualQuality();
  const [mode, setModeState] = useState(() => getRouteMode(location.pathname));
  const [chapterProgress, setChapterProgress] = useState(0);
  const [processingIntensity, setProcessingIntensity] = useState(0);
  const [scoreTarget, setScoreTarget] = useState(null);

  useEffect(() => {
    setModeState(getRouteMode(location.pathname));
    window.scrollTo({ top: 0, behavior: "auto" });
  }, [location.pathname]);

  const setMode = useCallback((nextMode) => {
    setModeState(nextMode);
  }, []);

  const value = useMemo(
    () => ({
      mode,
      setMode,
      chapterProgress,
      setChapterProgress,
      processingIntensity,
      setProcessingIntensity,
      scoreTarget,
      setScoreTarget,
      qualityTier,
    }),
    [chapterProgress, mode, processingIntensity, qualityTier, scoreTarget, setMode],
  );

  return <VisualExperienceContext.Provider value={value}>{children}</VisualExperienceContext.Provider>;
}

export function useVisualExperience() {
  const value = useContext(VisualExperienceContext);
  if (!value) throw new Error("useVisualExperience must be used within VisualExperienceProvider");
  return value;
}
