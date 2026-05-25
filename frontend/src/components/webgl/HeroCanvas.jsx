import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { Bloom, EffectComposer } from "@react-three/postprocessing";
import { Suspense, useEffect, useRef, useState } from "react";
import * as THREE from "three";

import ScoreOrb from "./ScoreOrb.jsx";

function CameraRig() {
  const { camera } = useThree();
  const scrollRef = useRef(0);

  useFrame(() => {
    const scrollable = Math.max(document.documentElement.scrollHeight - window.innerHeight, 1);
    const raw = window.scrollY / scrollable;
    scrollRef.current += (raw - scrollRef.current) * 0.06;
    const progress = scrollRef.current;

    const targetZ = THREE.MathUtils.lerp(5.8, 4.2, THREE.MathUtils.smoothstep(progress, 0, 0.9));
    camera.position.z = THREE.MathUtils.lerp(camera.position.z, targetZ, 0.06);
    camera.position.y = THREE.MathUtils.lerp(camera.position.y, -progress * 0.3, 0.06);
    camera.lookAt(0, -0.1, 0);
  });

  return null;
}

function OrbitingLight() {
  const ref = useRef(null);

  useFrame((state) => {
    const t = state.clock.getElapsedTime();
    if (ref.current) {
      ref.current.position.x = Math.cos(t * 0.5) * 4;
      ref.current.position.z = Math.sin(t * 0.5) * 4;
      ref.current.position.y = Math.sin(t * 0.3) * 1.5;
    }
  });

  return <pointLight ref={ref} color="#D4A853" intensity={2} distance={10} decay={1.5} />;
}

export default function HeroCanvas() {
  const [active, setActive] = useState(true);

  useEffect(() => {
    const check = () => {
      // Only render on root path
      const hash = window.location.hash;
      const path = window.location.pathname;
      setActive(path === "/" || path === "");
    };

    check();
    window.addEventListener("popstate", check);
    window.addEventListener("hashchange", check);

    return () => {
      window.removeEventListener("popstate", check);
      window.removeEventListener("hashchange", check);
    };
  }, []);

  if (!active) return null;

  return (
    <div
      className="hero-canvas-container"
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 2,
        pointerEvents: "none",
      }}
    >
      <Canvas
        gl={{
          antialias: true,
          alpha: true,
          powerPreference: "high-performance",
          stencil: false,
        }}
        camera={{ position: [0, 0, 5.8], fov: 42, near: 0.1, far: 30 }}
        dpr={[1, 2]}
        style={{ width: "100%", height: "100%" }}
      >
        <Suspense fallback={null}>
          <ambientLight intensity={0.35} />
          <OrbitingLight />
          <ScoreOrb />
          <CameraRig />

          {/* Only Bloom — lightweight, no chromatic aberration / noise / vignette */}
          <EffectComposer multisampling={0}>
            <Bloom threshold={0.5} strength={0.4} radius={0.7} />
          </EffectComposer>
        </Suspense>
      </Canvas>
    </div>
  );
}
