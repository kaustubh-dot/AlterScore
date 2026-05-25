import { useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import * as THREE from "three";

export default function ScoreOrb() {
  const meshRef = useRef(null);
  const wireRef = useRef(null);
  const glowRef = useRef(null);

  // Single clean icosahedron — no split, no particles
  const geometry = useMemo(() => new THREE.IcosahedronGeometry(1.5, 2), []);
  const edgeGeom = useMemo(() => new THREE.EdgesGeometry(geometry), [geometry]);

  // Cached scroll value to avoid DOM reads every frame
  const scrollState = useRef({ progress: 0, morph: 0 });

  useFrame((state) => {
    const time = state.clock.getElapsedTime();

    // Read scroll once per frame
    const scrollable = Math.max(document.documentElement.scrollHeight - window.innerHeight, 1);
    const rawProgress = window.scrollY / scrollable;
    // Smooth interpolation to avoid jerky updates
    scrollState.current.progress += (rawProgress - scrollState.current.progress) * 0.06;
    const progress = scrollState.current.progress;

    // Morph: flatten on Y axis as user scrolls through manifesto
    const morph = THREE.MathUtils.smoothstep(progress, 0.15, 0.45);
    scrollState.current.morph = morph;

    // Gentle continuous rotation + scroll-scrub
    const rotY = time * 0.15 + progress * Math.PI;
    const rotX = time * 0.06 + progress * 0.4;

    if (meshRef.current) {
      meshRef.current.rotation.y = rotY;
      meshRef.current.rotation.x = rotX;
      meshRef.current.scale.set(1, THREE.MathUtils.lerp(1, 0.3, morph), 1);
    }
    if (wireRef.current) {
      wireRef.current.rotation.y = rotY;
      wireRef.current.rotation.x = rotX;
      wireRef.current.scale.set(1, THREE.MathUtils.lerp(1, 0.3, morph), 1);
    }

    // Fade out the orb as user scrolls past pillars
    const fadeOut = 1 - THREE.MathUtils.smoothstep(progress, 0.65, 0.85);
    if (glowRef.current) {
      glowRef.current.opacity = 0.08 * fadeOut;
    }
    if (wireRef.current && wireRef.current.material) {
      wireRef.current.material.opacity = 0.45 * fadeOut;
    }
  });

  return (
    <group position={[0, 0, 0]}>
      {/* Translucent glass inner fill */}
      <mesh ref={meshRef} geometry={geometry}>
        <meshStandardMaterial
          ref={glowRef}
          color="#D4A853"
          transparent
          opacity={0.08}
          roughness={0.2}
          metalness={0.9}
          side={THREE.DoubleSide}
        />
      </mesh>

      {/* Gold wireframe edges */}
      <lineSegments ref={wireRef} geometry={edgeGeom}>
        <lineBasicMaterial
          color="#D4A853"
          transparent
          opacity={0.45}
          blending={THREE.AdditiveBlending}
        />
      </lineSegments>
    </group>
  );
}
