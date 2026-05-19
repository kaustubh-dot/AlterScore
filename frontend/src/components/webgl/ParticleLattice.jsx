import { useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import * as THREE from "three";

const vertexShader = `
  uniform float uTime;
  uniform float uMorph;
  uniform float uSizeScale;
  attribute float aRandom;
  attribute vec3 aDisc;
  varying float vRandom;
  varying float vPulse;

  void main() {
    vec3 sphere = position;
    vec3 disc = aDisc;
    vec3 pos = mix(sphere, disc, smoothstep(0.0, 1.0, uMorph));
    float drift = sin(uTime * 0.45 + aRandom * 18.0);
    pos.x += drift * 0.045 * (1.0 - uMorph);
    pos.y += cos(uTime * 0.35 + aRandom * 22.0) * 0.05;
    pos.z += sin(uTime * 0.25 + position.x * 2.0) * 0.04;

    vec4 mvPosition = modelViewMatrix * vec4(pos, 1.0);
    gl_Position = projectionMatrix * mvPosition;
    gl_PointSize = (2.7 + aRandom * 3.4) * uSizeScale * (8.0 / -mvPosition.z);
    vRandom = aRandom;
    vPulse = 0.55 + 0.45 * sin(uTime * 1.8 + aRandom * 40.0);
  }
`;

const fragmentShader = `
  varying float vRandom;
  varying float vPulse;

  void main() {
    vec2 uv = gl_PointCoord - 0.5;
    float dist = length(uv);
    float alpha = smoothstep(0.5, 0.08, dist);
    vec3 violet = vec3(0.482, 0.361, 1.0);
    vec3 teal = vec3(0.239, 1.0, 0.784);
    vec3 color = mix(violet, teal, vRandom);
    color += vPulse * 0.16;
    gl_FragColor = vec4(color, alpha * (0.45 + vPulse * 0.45));
  }
`;

function randomSpherePoint(radius) {
  const u = Math.random();
  const v = Math.random();
  const theta = 2 * Math.PI * u;
  const phi = Math.acos(2 * v - 1);
  return [
    radius * Math.sin(phi) * Math.cos(theta),
    radius * Math.sin(phi) * Math.sin(theta),
    radius * Math.cos(phi),
  ];
}

export default function ParticleLattice({ mobile = false }) {
  const materialRef = useRef(null);
  const count = mobile ? 3000 : 8000;

  const geometry = useMemo(() => {
    const positions = new Float32Array(count * 3);
    const disc = new Float32Array(count * 3);
    const randoms = new Float32Array(count);

    for (let index = 0; index < count; index += 1) {
      const sphere = randomSpherePoint(2.4 + Math.random() * 0.9);
      positions[index * 3] = sphere[0];
      positions[index * 3 + 1] = sphere[1];
      positions[index * 3 + 2] = sphere[2];

      const angle = Math.PI * (0.04 + Math.random() * 0.92);
      const radius = 0.7 + Math.random() * 2.55;
      disc[index * 3] = Math.cos(angle) * radius;
      disc[index * 3 + 1] = Math.sin(angle) * radius * 0.78 - 1.15 + (Math.random() - 0.5) * 0.18;
      disc[index * 3 + 2] = (Math.random() - 0.5) * 0.28;
      randoms[index] = Math.random();
    }

    const buffer = new THREE.BufferGeometry();
    buffer.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    buffer.setAttribute("aDisc", new THREE.BufferAttribute(disc, 3));
    buffer.setAttribute("aRandom", new THREE.BufferAttribute(randoms, 1));
    return buffer;
  }, [count]);

  const uniforms = useMemo(
    () => ({
      uTime: { value: 0 },
      uMorph: { value: 0 },
      uSizeScale: { value: mobile ? 0.82 : 1 },
    }),
    [mobile],
  );

  useFrame((state) => {
    const scrollable = Math.max(document.documentElement.scrollHeight - window.innerHeight, 1);
    const progress = window.scrollY / scrollable;
    const morph = THREE.MathUtils.smoothstep(progress, 0.16, 0.42);
    if (materialRef.current) {
      materialRef.current.uniforms.uTime.value = state.clock.elapsedTime;
      materialRef.current.uniforms.uMorph.value = morph;
    }
  });

  return (
    <points geometry={geometry} position={[0, 0.42, 0]}>
      <shaderMaterial
        ref={materialRef}
        args={[
          {
            uniforms,
            vertexShader,
            fragmentShader,
            transparent: true,
            depthWrite: false,
            blending: THREE.AdditiveBlending,
          },
        ]}
      />
    </points>
  );
}
