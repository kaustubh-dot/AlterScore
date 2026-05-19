import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { Bloom, ChromaticAberration, EffectComposer, Noise } from "@react-three/postprocessing";
import { Suspense, useEffect, useState } from "react";
import * as THREE from "three";

import BackgroundGrid from "./BackgroundGrid.jsx";
import ParticleLattice from "./ParticleLattice.jsx";

function ScrollCameraRig() {
  const { camera } = useThree();

  useFrame(() => {
    const scrollable = Math.max(document.documentElement.scrollHeight - window.innerHeight, 1);
    const progress = window.scrollY / scrollable;
    camera.position.x = THREE.MathUtils.lerp(camera.position.x, progress * 0.8, 0.04);
    camera.position.y = THREE.MathUtils.lerp(camera.position.y, 1.1 - progress * 0.45, 0.04);
    camera.position.z = THREE.MathUtils.lerp(camera.position.z, 7.2 - progress * 2.2, 0.04);
    camera.lookAt(0, -0.2, 0);
  });

  return null;
}

function useMobileWebGL() {
  const [mobile, setMobile] = useState(() => window.innerWidth < 768);

  useEffect(() => {
    const onResize = () => setMobile(window.innerWidth < 768);
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  return mobile;
}

export default function BackgroundScene() {
  const mobile = useMobileWebGL();

  return (
    <div className="background-scene" aria-hidden="true">
      <Canvas
        gl={{ antialias: true, alpha: true, powerPreference: "high-performance" }}
        camera={{ position: [0, 1.1, 7.2], fov: 45, near: 0.1, far: 100 }}
        dpr={[1, mobile ? 1.25 : 1.8]}
      >
        <Suspense fallback={null}>
          <color attach="background" args={["#04050F"]} />
          <fog attach="fog" args={["#04050F", 7, 18]} />
          <ParticleLattice mobile={mobile} />
          {!mobile && <BackgroundGrid />}
          <ScrollCameraRig />
          <EffectComposer multisampling={0}>
            <Bloom threshold={0.6} strength={0.42} radius={0.82} />
            {!mobile && <ChromaticAberration offset={[0.0008, 0.0008]} />}
            <Noise opacity={0.02} />
          </EffectComposer>
        </Suspense>
      </Canvas>
    </div>
  );
}
