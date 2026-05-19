import { Canvas, useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import * as THREE from "three";

function Drift() {
  const pointsRef = useRef(null);
  const geometry = useMemo(() => {
    const count = 2000;
    const positions = new Float32Array(count * 3);
    for (let index = 0; index < count; index += 1) {
      positions[index * 3] = (Math.random() - 0.5) * 10;
      positions[index * 3 + 1] = (Math.random() - 0.5) * 7;
      positions[index * 3 + 2] = (Math.random() - 0.5) * 6;
    }
    const buffer = new THREE.BufferGeometry();
    buffer.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    return buffer;
  }, []);

  useFrame((state) => {
    if (!pointsRef.current) return;
    pointsRef.current.rotation.y = state.clock.elapsedTime * 0.025;
    pointsRef.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.08) * 0.08;
  });

  return (
    <points ref={pointsRef} geometry={geometry}>
      <pointsMaterial color="#3DFFC8" size={0.018} transparent opacity={0.15} depthWrite={false} />
    </points>
  );
}

export default function ResultsParticles() {
  return (
    <div className="results-particles" aria-hidden="true">
      <Canvas camera={{ position: [0, 0, 6], fov: 50 }} gl={{ alpha: true }} dpr={[1, 1.4]}>
        <Drift />
      </Canvas>
    </div>
  );
}
