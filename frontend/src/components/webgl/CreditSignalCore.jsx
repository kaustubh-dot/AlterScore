import { useFrame } from "@react-three/fiber";
import { Line } from "@react-three/drei";
import { useMemo, useRef } from "react";
import * as THREE from "three";

const vertexShader = `
  uniform float uTime;
  uniform float uPulse;
  varying vec3 vNormal;
  varying vec3 vPosition;

  void main() {
    vNormal = normalize(normalMatrix * normal);
    float wave = sin(position.x * 4.0 + uTime) * cos(position.y * 5.0 - uTime * 0.72);
    vec3 displaced = position + normal * wave * (0.06 + uPulse * 0.045);
    vPosition = displaced;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(displaced, 1.0);
  }
`;

const fragmentShader = `
  uniform float uTime;
  uniform float uPulse;
  uniform float uOpacity;
  varying vec3 vNormal;
  varying vec3 vPosition;

  void main() {
    float fresnel = pow(1.0 - abs(dot(normalize(vNormal), vec3(0.0, 0.0, 1.0))), 2.2);
    float inner = 0.35 + 0.15 * sin(uTime * 1.4 + vPosition.y * 5.0);
    vec3 navy = vec3(0.015, 0.09, 0.18);
    vec3 cyan = vec3(0.18, 0.96, 0.92);
    vec3 ice = vec3(0.62, 0.85, 1.0);
    vec3 color = mix(navy, cyan, fresnel);
    color = mix(color, ice, fresnel * (0.24 + uPulse * 0.18));
    gl_FragColor = vec4(color, (inner + fresnel * 0.78) * uOpacity);
  }
`;

function HaloRings({ mode, progress, reducedMotion }) {
  const group = useRef(null);

  useFrame((state, delta) => {
    if (!group.current || reducedMotion) return;
    const speed = mode === "processing" ? 1.45 : 0.34;
    group.current.rotation.x += delta * speed * 0.34;
    group.current.rotation.y += delta * speed * 0.48;
    group.current.rotation.z -= delta * speed * 0.2;
  });

  const resultScale = mode === "results" ? 0.78 : 1;
  return (
    <group ref={group} scale={resultScale + progress * 0.06}>
      {[1.42, 1.72, 2.02].map((radius, index) => (
        <mesh key={radius} rotation={[index * 0.68, index * 0.42, index * 0.9]}>
          <torusGeometry args={[radius, 0.012 + index * 0.004, 8, 128]} />
          <meshBasicMaterial
            color={index === 2 ? "#d7b86f" : index === 1 ? "#a9d8ff" : "#55f6e2"}
            opacity={0.36 - index * 0.07}
            transparent
            blending={THREE.AdditiveBlending}
          />
        </mesh>
      ))}
    </group>
  );
}

function BehavioralSignals({ progress, mode, reducedMotion }) {
  const group = useRef(null);
  const points = useMemo(
    () =>
      Array.from({ length: 27 }, (_, index) => {
        const theta = (index / 27) * Math.PI * 2;
        const phi = Math.acos(1 - (2 * (index + 0.5)) / 27);
        const radius = 2.25 + (index % 4) * 0.1;
        return new THREE.Vector3(
          Math.sin(phi) * Math.cos(theta) * radius,
          Math.cos(phi) * radius,
          Math.sin(phi) * Math.sin(theta) * radius,
        );
      }),
    [],
  );

  const trails = useMemo(
    () =>
      points.slice(0, 9).map((point, index) => {
        const mid = point.clone().multiplyScalar(0.46);
        mid.x += Math.sin(index * 1.7) * 0.38;
        mid.y += Math.cos(index * 1.3) * 0.26;
        return new THREE.CatmullRomCurve3([point, mid, new THREE.Vector3(0, 0, 0)])
          .getPoints(24);
      }),
    [points],
  );

  useFrame((state, delta) => {
    if (!group.current || reducedMotion) return;
    group.current.rotation.y += delta * (mode === "processing" ? 0.52 : 0.13);
    group.current.rotation.z = Math.sin(state.clock.elapsedTime * 0.22) * 0.12;
  });

  const opacity = mode === "assessment" ? 0.26 : 0.3 + progress * 0.46;
  return (
    <group ref={group} scale={0.84 + progress * 0.2}>
      {points.map((point, index) => (
        <mesh key={index} position={point}>
          <sphereGeometry args={[index % 6 === 0 ? 0.055 : 0.032, 12, 12]} />
          <meshBasicMaterial
            color={index % 5 === 0 ? "#d7b86f" : "#71f7e8"}
            opacity={opacity}
            transparent
          />
        </mesh>
      ))}
      {trails.map((trail, index) => (
        <Line
          key={index}
          points={trail}
          color={index % 4 === 0 ? "#d7b86f" : "#58e9ee"}
          lineWidth={0.48}
          opacity={opacity * 0.45}
          transparent
        />
      ))}
    </group>
  );
}

export default function CreditSignalCore({
  mode,
  progress,
  processingIntensity,
  reducedMotion,
  scoreTarget,
}) {
  const core = useRef(null);
  const material = useRef(null);
  const group = useRef(null);

  const uniforms = useMemo(
    () => ({
      uTime: { value: 0 },
      uPulse: { value: 0 },
      uOpacity: { value: 1 },
    }),
    [],
  );

  useFrame((state, delta) => {
    const time = state.clock.elapsedTime;
    const pulse = mode === "processing" ? processingIntensity + 0.7 : 0.12 + progress * 0.18;
    if (material.current) {
      material.current.uniforms.uTime.value = reducedMotion ? 0 : time;
      material.current.uniforms.uPulse.value = pulse;
      material.current.uniforms.uOpacity.value = mode === "assessment" ? 0.52 : 0.92;
    }
    if (core.current && !reducedMotion) {
      core.current.rotation.x += delta * 0.12;
      core.current.rotation.y += delta * (mode === "processing" ? 0.54 : 0.19);
    }
    if (group.current) {
      const targetScale = mode === "results" ? 0.74 : mode === "assessment" ? 0.76 : 0.98 + progress * 0.1;
      group.current.scale.lerp(new THREE.Vector3(targetScale, targetScale, targetScale), 0.06);
      if (mode === "results" && scoreTarget) {
        const scoreProgress = THREE.MathUtils.clamp((scoreTarget - 300) / 550, 0, 1);
        group.current.rotation.z = THREE.MathUtils.lerp(group.current.rotation.z, scoreProgress * Math.PI, 0.045);
      }
    }
  });

  return (
    <group ref={group}>
      <mesh ref={core}>
        <icosahedronGeometry args={[1.02, 5]} />
        <shaderMaterial
          ref={material}
          vertexShader={vertexShader}
          fragmentShader={fragmentShader}
          uniforms={uniforms}
          transparent
          depthWrite={false}
          blending={THREE.AdditiveBlending}
        />
      </mesh>
      <HaloRings mode={mode} progress={progress} reducedMotion={reducedMotion} />
      <BehavioralSignals mode={mode} progress={progress} reducedMotion={reducedMotion} />
    </group>
  );
}
