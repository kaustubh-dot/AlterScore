import { Canvas } from "@react-three/fiber";
import { Line, Sphere } from "@react-three/drei";
import { Bloom, EffectComposer } from "@react-three/postprocessing";
import { useEffect, useMemo, useState } from "react";
import { gsap } from "gsap";
import * as THREE from "three";

function Arc({ score }) {
  const [progress, setProgress] = useState(0);
  const normalized = Math.min(Math.max((Number(score) - 300) / 550, 0), 1);

  useEffect(() => {
    const state = { value: 0 };
    const tween = gsap.to(state, {
      value: normalized,
      duration: 2,
      delay: 0.8,
      ease: "power3.out",
      onUpdate: () => setProgress(state.value),
    });
    return () => tween.kill();
  }, [normalized]);

  const points = useMemo(() => {
    const total = 180;
    const visible = Math.max(2, Math.floor(total * progress));
    return Array.from({ length: visible }, (_, index) => {
      const t = index / (total - 1);
      const angle = Math.PI * (1 - t);
      return new THREE.Vector3(Math.cos(angle) * 2.65, Math.sin(angle) * 2.65 - 1.05, 0);
    });
  }, [progress]);

  const tip = points[points.length - 1] || new THREE.Vector3(-2.65, -1.05, 0);

  return (
    <>
      <Line
        points={points}
        color="#3DFFC8"
        lineWidth={4}
        transparent
        opacity={0.95}
      />
      <Line
        points={Array.from({ length: 180 }, (_, index) => {
          const t = index / 179;
          const angle = Math.PI * (1 - t);
          return new THREE.Vector3(Math.cos(angle) * 2.65, Math.sin(angle) * 2.65 - 1.05, -0.02);
        })}
        color="#7B5CFF"
        lineWidth={1}
        transparent
        opacity={0.18}
      />
      <Sphere args={[0.09, 24, 24]} position={tip}>
        <meshBasicMaterial color="#3DFFC8" />
      </Sphere>
    </>
  );
}

export default function GaugeArc({ score }) {
  return (
    <div className="gauge-arc-canvas" aria-hidden="true">
      <Canvas camera={{ position: [0, 0, 6.2], fov: 50 }} dpr={[1, 1.6]} gl={{ alpha: true, antialias: true }}>
        <Arc score={score} />
        <EffectComposer multisampling={0}>
          <Bloom threshold={0.2} strength={0.55} radius={0.75} />
        </EffectComposer>
      </Canvas>
    </div>
  );
}
