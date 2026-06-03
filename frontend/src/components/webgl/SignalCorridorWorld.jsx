import { Line } from "@react-three/drei";
import { useFrame, useThree } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import * as THREE from "three";

import { useVisualExperience } from "../../context/VisualExperienceContext.jsx";

const SIGNAL_GLYPHS = [
  "ALTERSCORE / 027 SIGNALS / BUREAU GAP / BEHAVIORAL CONTEXT",
  "₹ FLOW / RESILIENCE / FUTURE ORIENTATION / RISK BAND",
  "STACKING ENSEMBLE / SHAP VECTOR / COUNTERFACTUAL PATH",
];

function makeGlyphTexture(seed) {
  const canvas = document.createElement("canvas");
  canvas.width = 1024;
  canvas.height = 256;
  const context = canvas.getContext("2d");
  context.clearRect(0, 0, canvas.width, canvas.height);
  context.fillStyle = "rgba(125, 207, 255, 0.08)";
  context.fillRect(0, 0, canvas.width, canvas.height);
  context.font = "28px monospace";
  context.textBaseline = "top";

  for (let row = 0; row < 7; row += 1) {
    context.fillStyle = row % 3 === 0 ? "rgba(89, 244, 225, 0.72)" : "rgba(207, 237, 255, 0.5)";
    const text = `${SIGNAL_GLYPHS[(seed + row) % SIGNAL_GLYPHS.length]} // ${String(seed * 17 + row).padStart(4, "0")}`;
    context.fillText(text.repeat(2), -seed * 37 + row * 19, row * 36);
  }

  const texture = new THREE.CanvasTexture(canvas);
  texture.wrapS = THREE.RepeatWrapping;
  texture.wrapT = THREE.ClampToEdgeWrapping;
  texture.needsUpdate = true;
  return texture;
}

function CorridorCamera({ progress, reducedMotion }) {
  const { camera } = useThree();
  const pointer = useRef(new THREE.Vector2());
  const curve = useMemo(
    () =>
      new THREE.CatmullRomCurve3([
        new THREE.Vector3(0.8, 0.35, 9),
        new THREE.Vector3(-1.5, 0.22, -3),
        new THREE.Vector3(1.75, 0.05, -15),
        new THREE.Vector3(-0.85, -0.08, -29),
        new THREE.Vector3(0.45, 0.08, -43),
        new THREE.Vector3(0, 0.16, -58),
      ]),
    [],
  );

  useFrame((state) => {
    pointer.current.x = THREE.MathUtils.lerp(pointer.current.x, state.pointer.x, 0.035);
    pointer.current.y = THREE.MathUtils.lerp(pointer.current.y, state.pointer.y, 0.035);

    const t = reducedMotion ? 0.9 : THREE.MathUtils.clamp(progress, 0, 1);
    const position = curve.getPoint(t);
    const lookAt = curve.getPoint(Math.min(t + 0.035, 1));
    const drift = reducedMotion ? 0 : 0.22;
    position.x += pointer.current.x * drift;
    position.y += pointer.current.y * drift * 0.45;

    camera.position.lerp(position, 0.075);
    camera.lookAt(lookAt.x, lookAt.y, lookAt.z - 1.4);
    camera.rotation.z = THREE.MathUtils.lerp(camera.rotation.z, Math.sin(t * Math.PI * 2.35) * 0.055, 0.06);
  });

  return null;
}

function PointFog({ count, reducedMotion }) {
  const ref = useRef(null);
  const positions = useMemo(() => {
    const values = new Float32Array(count * 3);
    for (let index = 0; index < count; index += 1) {
      const z = 8 - Math.random() * 72;
      const radius = 2.2 + Math.random() * 5.8;
      const angle = Math.random() * Math.PI * 2;
      values[index * 3] = Math.cos(angle) * radius;
      values[index * 3 + 1] = (Math.random() - 0.48) * 5.4;
      values[index * 3 + 2] = z;
    }
    return values;
  }, [count]);

  useFrame((_, delta) => {
    if (!ref.current || reducedMotion) return;
    ref.current.rotation.z += delta * 0.006;
  });

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <pointsMaterial
        color="#9de9ff"
        opacity={0.34}
        size={0.032}
        sizeAttenuation
        transparent
        depthWrite={false}
      />
    </points>
  );
}

function CorridorRails({ reducedMotion }) {
  const group = useRef(null);
  const rails = useMemo(() => {
    const offsets = [
      [-2.5, -1.25],
      [2.5, -1.25],
      [-3.9, 1.2],
      [3.9, 1.2],
    ];
    return offsets.map(([x, y], index) => {
      const points = [];
      for (let step = 0; step < 34; step += 1) {
        const z = 7 - step * 2.05;
        points.push(new THREE.Vector3(x + Math.sin(step * 0.34 + index) * 0.18, y, z));
      }
      return points;
    });
  }, []);

  useFrame((_, delta) => {
    if (!group.current || reducedMotion) return;
    group.current.position.z = Math.sin(delta * 0.001) * 0.02;
  });

  return (
    <group ref={group}>
      {rails.map((points, index) => (
        <Line
          key={index}
          points={points}
          color={index < 2 ? "#59f4e1" : "#d7b86f"}
          lineWidth={index < 2 ? 1.4 : 0.68}
          transparent
          opacity={index < 2 ? 0.82 : 0.42}
        />
      ))}
    </group>
  );
}

function DataRibbons({ reducedMotion }) {
  const group = useRef(null);
  const ribbons = useMemo(
    () =>
      Array.from({ length: 5 }, (_, index) => {
        const points = [];
        for (let step = 0; step < 70; step += 1) {
          const z = 7 - step * 0.9;
          const wave = Math.sin(step * 0.26 + index * 0.8);
          points.push(new THREE.Vector3(wave * (1.2 + index * 0.25), -0.4 + Math.cos(step * 0.18 + index) * 0.42, z));
        }
        return points;
      }),
    [],
  );

  useFrame((_, delta) => {
    if (!group.current || reducedMotion) return;
    group.current.rotation.z += delta * 0.01;
  });

  return (
    <group ref={group}>
      {ribbons.map((points, index) => (
        <Line
          key={index}
          points={points}
          color={index % 2 === 0 ? "#7dcfff" : "#59f4e1"}
          lineWidth={0.82}
          transparent
          opacity={0.38}
        />
      ))}
    </group>
  );
}

function GlassSlabs({ progress, reducedMotion }) {
  const group = useRef(null);
  const slabs = useMemo(
    () =>
      Array.from({ length: 18 }, (_, index) => ({
        x: index % 2 === 0 ? -2.15 - (index % 3) * 0.55 : 2.15 + (index % 3) * 0.55,
        y: -0.15 + ((index % 5) - 2) * 0.18,
        z: 1.5 - index * 3.4,
        h: 1.8 + (index % 4) * 0.54,
        w: 0.92 + (index % 3) * 0.38,
        r: index % 2 === 0 ? -0.18 : 0.18,
      })),
    [],
  );

  useFrame((_, delta) => {
    if (!group.current || reducedMotion) return;
    group.current.children.forEach((child, index) => {
      child.rotation.y += delta * (index % 2 === 0 ? 0.025 : -0.018);
    });
  });

  return (
    <group ref={group}>
      {slabs.map((slab, index) => (
        <mesh key={index} position={[slab.x, slab.y, slab.z]} rotation={[0.05, slab.r, 0]}>
          <boxGeometry args={[slab.w, slab.h, 0.028]} />
          <meshPhysicalMaterial
            color={index % 4 === 0 ? "#d7b86f" : "#89eaff"}
            emissive={index % 4 === 0 ? "#5b451d" : "#063c45"}
            emissiveIntensity={0.18 + progress * 0.18}
            opacity={0.2}
            roughness={0.2}
            metalness={0.2}
            transparent
            transmission={0.4}
            depthWrite={false}
          />
        </mesh>
      ))}
    </group>
  );
}

function TunnelFrames({ reducedMotion }) {
  const group = useRef(null);
  const frames = useMemo(
    () =>
      Array.from({ length: 17 }, (_, index) => ({
        z: 3 - index * 3.9,
        radius: 3.05 + (index % 3) * 0.22,
        rotation: index * 0.19,
        color: index % 5 === 0 ? "#d7b86f" : index % 2 === 0 ? "#59f4e1" : "#7dcfff",
      })),
    [],
  );

  useFrame((_, delta) => {
    if (!group.current || reducedMotion) return;
    group.current.rotation.z += delta * 0.018;
  });

  return (
    <group ref={group}>
      {frames.map((frame, index) => (
        <mesh key={index} position={[0, 0, frame.z]} rotation={[0, 0, frame.rotation]}>
          <torusGeometry args={[frame.radius, index % 5 === 0 ? 0.026 : 0.016, 6, 72]} />
          <meshBasicMaterial
            color={frame.color}
            opacity={index % 5 === 0 ? 0.3 : 0.16}
            transparent
            depthWrite={false}
            blending={THREE.AdditiveBlending}
          />
        </mesh>
      ))}
    </group>
  );
}

function CipherPlanes({ reducedMotion }) {
  const group = useRef(null);
  const textures = useMemo(() => [makeGlyphTexture(1), makeGlyphTexture(2), makeGlyphTexture(3)], []);
  const planes = useMemo(
    () => [
      { texture: textures[0], position: [-2.7, 1.2, -8], rotation: [0, 0.55, 0.04], scale: [3.1, 0.78, 1] },
      { texture: textures[1], position: [2.65, -0.75, -22], rotation: [0, -0.48, -0.02], scale: [3.4, 0.82, 1] },
      { texture: textures[2], position: [-1.15, 1.55, -39], rotation: [0.08, 0.18, -0.05], scale: [4.1, 0.94, 1] },
    ],
    [textures],
  );

  useFrame((_, delta) => {
    if (reducedMotion) return;
    textures.forEach((texture, index) => {
      texture.offset.x += delta * (0.01 + index * 0.006);
    });
    if (group.current) group.current.rotation.z = Math.sin(Date.now() * 0.0002) * 0.018;
  });

  return (
    <group ref={group}>
      {planes.map((plane, index) => (
        <mesh key={index} position={plane.position} rotation={plane.rotation} scale={plane.scale}>
          <planeGeometry args={[2.8, 0.86]} />
          <meshBasicMaterial map={plane.texture} transparent opacity={0.42} depthWrite={false} blending={THREE.AdditiveBlending} />
        </mesh>
      ))}
    </group>
  );
}

function SignalNodes({ progress, reducedMotion }) {
  const group = useRef(null);
  const nodes = useMemo(
    () =>
      Array.from({ length: 27 }, (_, index) => {
        const z = -5 - index * 1.38;
        const angle = index * 1.15;
        const radius = 1.35 + (index % 4) * 0.22;
        return {
          position: [Math.cos(angle) * radius, Math.sin(angle) * 0.72, z],
          color: index % 7 === 0 ? "#d7b86f" : "#59f4e1",
          size: index % 7 === 0 ? 0.085 : 0.052,
        };
      }),
    [],
  );

  useFrame((_, delta) => {
    if (!group.current || reducedMotion) return;
    group.current.rotation.z += delta * 0.06;
  });

  return (
    <group ref={group} scale={0.92 + progress * 0.14}>
      {nodes.map((node, index) => (
        <mesh key={index} position={node.position}>
          <sphereGeometry args={[node.size, 14, 14]} />
          <meshBasicMaterial color={node.color} transparent opacity={0.72} blending={THREE.AdditiveBlending} />
        </mesh>
      ))}
    </group>
  );
}

function ScoreRings({ progress, reducedMotion }) {
  const group = useRef(null);
  const reveal = THREE.MathUtils.smoothstep(progress, 0.48, 0.86);

  useFrame((_, delta) => {
    if (!group.current || reducedMotion) return;
    group.current.rotation.z += delta * 0.08;
    group.current.rotation.y = THREE.MathUtils.lerp(group.current.rotation.y, Math.PI * 0.08, 0.04);
  });

  return (
    <group ref={group} position={[0, 0.02, -49]} scale={1.4 + reveal * 0.55}>
      {[1.1, 1.55, 2].map((radius, index) => (
        <mesh key={radius} rotation={[Math.PI / 2, 0, index * 0.75]}>
          <torusGeometry args={[radius, 0.018 + index * 0.006, 8, 160, Math.PI * 1.58]} />
          <meshBasicMaterial
            color={index === 2 ? "#d7b86f" : index === 1 ? "#7dcfff" : "#59f4e1"}
            transparent
            opacity={(0.34 + index * 0.16) * reveal}
            blending={THREE.AdditiveBlending}
          />
        </mesh>
      ))}
    </group>
  );
}

function HorizonPanels() {
  return (
    <group position={[0, -1.85, -31]} rotation={[-Math.PI / 2, 0, 0]}>
      <mesh>
        <planeGeometry args={[16, 68, 1, 1]} />
        <meshBasicMaterial color="#071426" transparent opacity={0.28} />
      </mesh>
      <gridHelper args={[18, 44, "#59f4e1", "#1b5d70"]} position={[0, 0.01, 0]} />
    </group>
  );
}

export default function SignalCorridorWorld() {
  const { chapterProgress, qualityTier } = useVisualExperience();
  const count = Math.max(qualityTier.name === "mobile" ? 360 : qualityTier.particleCount, 360);
  const reducedMotion = qualityTier.reducedMotion;

  return (
    <>
      <color attach="background" args={["#030916"]} />
      <fog attach="fog" args={["#030916", 8, 58]} />
      <ambientLight intensity={0.18} />
      <pointLight position={[0, 1.2, -8]} color="#59f4e1" intensity={1.8} distance={18} />
      <pointLight position={[3, -0.8, -36]} color="#d7b86f" intensity={1.1} distance={16} />
      <PointFog count={count} reducedMotion={reducedMotion} />
      <HorizonPanels />
      <TunnelFrames reducedMotion={reducedMotion} />
      <CorridorRails reducedMotion={reducedMotion} />
      <DataRibbons reducedMotion={reducedMotion} />
      <GlassSlabs progress={chapterProgress} reducedMotion={reducedMotion} />
      <CipherPlanes reducedMotion={reducedMotion} />
      <SignalNodes progress={chapterProgress} reducedMotion={reducedMotion} />
      <ScoreRings progress={chapterProgress} reducedMotion={reducedMotion} />
      <CorridorCamera progress={chapterProgress} reducedMotion={reducedMotion} />
    </>
  );
}
