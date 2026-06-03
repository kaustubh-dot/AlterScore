import { useEffect, useMemo, useState } from "react";

function readEnvironment() {
  const width = window.innerWidth;
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const coarsePointer = window.matchMedia("(pointer: coarse)").matches;

  if (width <= 700) {
    return {
      name: "mobile",
      particleCount: 480,
      terrainSegments: 32,
      dpr: 1,
      bloom: false,
      reducedMotion,
      coarsePointer,
    };
  }

  if (width <= 1100) {
    return {
      name: "tablet",
      particleCount: 1100,
      terrainSegments: 64,
      dpr: Math.min(window.devicePixelRatio || 1, 1.25),
      bloom: !reducedMotion,
      reducedMotion,
      coarsePointer,
    };
  }

  return {
    name: "desktop",
    particleCount: 2200,
    terrainSegments: 128,
    dpr: Math.min(window.devicePixelRatio || 1, 1.5),
    bloom: !reducedMotion,
    reducedMotion,
    coarsePointer,
  };
}

export default function useVisualQuality() {
  const [environment, setEnvironment] = useState(readEnvironment);

  useEffect(() => {
    const reducedMotionQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    const pointerQuery = window.matchMedia("(pointer: coarse)");
    const update = () => setEnvironment(readEnvironment());

    window.addEventListener("resize", update);
    reducedMotionQuery.addEventListener("change", update);
    pointerQuery.addEventListener("change", update);

    return () => {
      window.removeEventListener("resize", update);
      reducedMotionQuery.removeEventListener("change", update);
      pointerQuery.removeEventListener("change", update);
    };
  }, []);

  return useMemo(() => environment, [environment]);
}
