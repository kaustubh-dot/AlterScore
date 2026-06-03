import { Line } from "@react-three/drei";
import { useFrame, useThree } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import * as THREE from "three";

import { useVisualExperience } from "../../context/VisualExperienceContext.jsx";

// Camera Spline definition from Space (Z=50) to Access Chamber (Z=-240)
const splinePoints = [
  new THREE.Vector3(0, 0, 50),         // Start in near-black space
  new THREE.Vector3(0, 0.35, 20),      // Corridor entry
  new THREE.Vector3(0, 0.35, -15),     // Chapter 1 Origin Pause
  new THREE.Vector3(-1.2, 0.45, -45),   // Entering behavioral field (curved)
  new THREE.Vector3(1.2, -0.25, -80),   // Chapter 2 Behavioral Pause
  new THREE.Vector3(0, 0.15, -115),     // Chapter 3 Ensemble Pause
  new THREE.Vector3(-0.7, -0.15, -150),  // Entering SHAP tunnel
  new THREE.Vector3(0.7, 0.15, -185),   // Chapter 4 SHAP Tunnel Pause
  new THREE.Vector3(0, 0, -220),       // Chapter 5 Access Chamber Pause
  new THREE.Vector3(0, 0, -240),       // Final resting spot
];
const cameraSpline = new THREE.CatmullRomCurve3(splinePoints);

function CameraRig({ progress, reducedMotion }) {
  const { camera } = useThree();
  const pointer = useRef(new THREE.Vector2());

  useFrame((state) => {
    // Parallax mouse drift
    pointer.current.x = THREE.MathUtils.lerp(pointer.current.x, state.pointer.x, 0.03);
    pointer.current.y = THREE.MathUtils.lerp(pointer.current.y, state.pointer.y, 0.03);

    const t = THREE.MathUtils.clamp(progress, 0, 1);
    const position = cameraSpline.getPoint(t);
    const lookAtTarget = cameraSpline.getPoint(Math.min(t + 0.022, 1));

    const drift = reducedMotion ? 0 : 0.28;
    position.x += pointer.current.x * drift;
    position.y += pointer.current.y * drift * 0.45;

    camera.position.copy(position);
    camera.lookAt(lookAtTarget.x, lookAtTarget.y, lookAtTarget.z - 1.2);
    
    // Add cinematic roll based on spline curves
    camera.rotation.z = THREE.MathUtils.lerp(
      camera.rotation.z, 
      reducedMotion ? 0 : Math.sin(t * Math.PI * 3.2) * 0.045, 
      0.05
    );
  });

  return null;
}

// Particle field spanning the entire scene
function SpaceParticles({ count, reducedMotion }) {
  const ref = useRef(null);
  const positions = useMemo(() => {
    const values = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      const z = 60 - Math.random() * 320;
      const radius = 1.8 + Math.random() * 6.5;
      const angle = Math.random() * Math.PI * 2;
      values[i * 3] = Math.cos(angle) * radius;
      values[i * 3 + 1] = (Math.random() - 0.5) * 6;
      values[i * 3 + 2] = z;
    }
    return values;
  }, [count]);

  useFrame((_, delta) => {
    if (!ref.current || reducedMotion) return;
    ref.current.rotation.z += delta * 0.005;
  });

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <pointsMaterial
        color="#7DCFFF"
        opacity={0.3}
        size={0.024}
        sizeAttenuation
        transparent
        depthWrite={false}
      />
    </points>
  );
}

// Rails running parallel to the camera path
function CorridorRails({ reducedMotion }) {
  const rails = useMemo(() => {
    const leftPoints = [];
    const rightPoints = [];
    const samples = 120;
    for (let i = 0; i <= samples; i++) {
      const t = i / samples;
      const p = cameraSpline.getPoint(t);
      leftPoints.push(new THREE.Vector3(p.x - 0.65, p.y - 0.35, p.z));
      rightPoints.push(new THREE.Vector3(p.x + 0.65, p.y - 0.35, p.z));
    }
    return { leftPoints, rightPoints };
  }, []);

  return (
    <group>
      <Line
        points={rails.leftPoints}
        color="#59F4E1"
        lineWidth={1.0}
        transparent
        opacity={0.7}
      />
      <Line
        points={rails.rightPoints}
        color="#7DCFFF"
        lineWidth={1.0}
        transparent
        opacity={0.5}
      />
    </group>
  );
}

// Chapter 1: Abstract Corridor & Slabs
function CorridorCorridor({ qualityTier }) {
  const frames = useMemo(() => {
    const arr = [];
    const count = qualityTier.name === "mobile" ? 6 : 14;
    for (let i = 0; i < count; i++) {
      const z = 30 - i * 4.5;
      arr.push({ z, scale: [4.2, 3.2, 0.1] });
    }
    return arr;
  }, [qualityTier]);

  const slabs = useMemo(() => {
    const arr = [];
    const count = qualityTier.name === "mobile" ? 4 : 10;
    for (let i = 0; i < count; i++) {
      const z = 20 - i * 6;
      arr.push({
        x: i % 2 === 0 ? -1.8 : 1.8,
        y: (Math.random() - 0.5) * 0.8,
        z,
        w: 0.8 + Math.random() * 0.5,
        h: 1.4 + Math.random() * 0.8,
        rot: (Math.random() - 0.5) * 0.3,
      });
    }
    return arr;
  }, [qualityTier]);

  return (
    <group>
      {/* Rectangular tunnel frames */}
      {frames.map((frame, i) => (
        <group key={`f-${i}`} position={[0, 0.25, frame.z]}>
          <Line
            points={[
              new THREE.Vector3(-frame.scale[0] / 2, -frame.scale[1] / 2, 0),
              new THREE.Vector3(frame.scale[0] / 2, -frame.scale[1] / 2, 0),
              new THREE.Vector3(frame.scale[0] / 2, frame.scale[1] / 2, 0),
              new THREE.Vector3(-frame.scale[0] / 2, frame.scale[1] / 2, 0),
              new THREE.Vector3(-frame.scale[0] / 2, -frame.scale[1] / 2, 0),
            ]}
            color="#7DCFFF"
            lineWidth={0.5}
            transparent
            opacity={0.18}
          />
        </group>
      ))}

      {/* Floating glass fragments */}
      {slabs.map((slab, i) => (
        <mesh key={`s-${i}`} position={[slab.x, slab.y, slab.z]} rotation={[0, slab.rot, 0.05]}>
          <boxGeometry args={[slab.w, slab.h, 0.02]} />
          {qualityTier.name === "mobile" ? (
            <meshBasicMaterial color="#7DCFFF" opacity={0.12} transparent depthWrite={false} />
          ) : (
            <meshPhysicalMaterial
              color="#7DCFFF"
              roughness={0.1}
              metalness={0.1}
              transparent
              opacity={0.18}
              transmission={0.4}
              depthWrite={false}
            />
          )}
        </mesh>
      ))}
    </group>
  );
}

// Chapter 2: 27 Luminous orbiting nodes
function BehavioralNodes({ qualityTier }) {
  const count = qualityTier.name === "mobile" ? 15 : 27;
  const nodes = useMemo(() => {
    const arr = [];
    for (let i = 0; i < count; i++) {
      const t = 0.22 + (i / count) * 0.16;
      const p = cameraSpline.getPoint(t);
      const angle = i * 1.95;
      const r = 1.4 + (i % 3) * 0.35;
      arr.push({
        pos: new THREE.Vector3(p.x + Math.cos(angle) * r, p.y + Math.sin(angle) * r, p.z),
        color: i % 3 === 0 ? "#59F4E1" : i % 3 === 1 ? "#7DCFFF" : "#D7B86F",
        size: 0.06 + (i % 3) * 0.02,
        orbitSpeed: (Math.random() - 0.5) * 0.6,
        angle,
        r,
        t,
      });
    }
    return arr;
  }, [count]);

  const groupRef = useRef(null);

  useFrame((state) => {
    if (!groupRef.current) return;
    const time = state.clock.getElapsedTime();
    const camPos = state.camera.position;

    groupRef.current.children.forEach((mesh, idx) => {
      const node = nodes[idx];
      if (!node) return;

      const currentAngle = node.angle + time * node.orbitSpeed * 0.2;
      const p = cameraSpline.getPoint(node.t);
      mesh.position.x = p.x + Math.cos(currentAngle) * node.r;
      mesh.position.y = p.y + Math.sin(currentAngle) * node.r;

      const dist = mesh.position.distanceTo(camPos);
      const isClose = dist < 7;
      const scaleTarget = isClose ? 1.9 + Math.sin(time * 9) * 0.45 : 1.0;
      mesh.scale.setScalar(THREE.MathUtils.lerp(mesh.scale.x, scaleTarget, 0.08));

      if (mesh.material) {
        mesh.material.opacity = isClose ? 0.95 : 0.42;
      }
    });
  });

  const connectionPaths = useMemo(() => {
    const paths = [];
    for (let i = 0; i < nodes.length - 1; i++) {
      if (i % 3 !== 0) {
        paths.push([nodes[i].pos, nodes[i + 1].pos]);
      }
    }
    return paths;
  }, [nodes]);

  return (
    <group ref={groupRef}>
      {nodes.map((node, i) => (
        <mesh key={i} position={node.pos}>
          <sphereGeometry args={[node.size, 12, 12]} />
          <meshBasicMaterial color={node.color} transparent opacity={0.4} blending={THREE.AdditiveBlending} />
        </mesh>
      ))}

      {connectionPaths.map((pts, i) => (
        <Line
          key={`l-${i}`}
          points={pts}
          color="#7DCFFF"
          lineWidth={0.5}
          transparent
          opacity={0.15}
        />
      ))}
    </group>
  );
}

// Chapter 3: Stacked model planes and converging signal streams
function ModelEnsemble({ qualityTier }) {
  const planes = useMemo(() => {
    const arr = [];
    const count = 6;
    for (let i = 0; i < count; i++) {
      arr.push({ z: -100 - i * 5 });
    }
    return arr;
  }, []);

  const streams = useMemo(() => {
    const arr = [];
    const startZ = -95;
    const endZ = -132;
    const endX = 0;
    const endY = 0.2;
    const count = 6;
    const colors = ["#59F4E1", "#7DCFFF", "#D7B86F", "#59F4E1", "#7DCFFF", "#D7B86F"];

    for (let index = 0; index < count; index++) {
      const angle = (index * Math.PI) / 3;
      const startX = Math.cos(angle) * 2.2;
      const startY = Math.sin(angle) * 2.2;
      const points = [];
      const steps = 24;
      for (let step = 0; step <= steps; step++) {
        const t = step / steps;
        const x = THREE.MathUtils.lerp(startX, endX, t) + Math.sin(t * Math.PI) * 0.35;
        const y = THREE.MathUtils.lerp(startY, endY, t) + Math.cos(t * Math.PI) * 0.35;
        const z = THREE.MathUtils.lerp(startZ, endZ, t);
        points.push(new THREE.Vector3(x, y, z));
      }
      arr.push({ points, color: colors[index] });
    }
    return arr;
  }, []);

  return (
    <group>
      {/* 6 Layered planes */}
      {planes.map((p, i) => (
        <mesh key={`p-${i}`} position={[0, 0, p.z]} rotation={[0.04, 0.05, 0]}>
          <planeGeometry args={[3.2, 3.2]} />
          {qualityTier.name === "mobile" ? (
            <meshBasicMaterial color="#7DCFFF" opacity={0.08} transparent depthWrite={false} />
          ) : (
            <meshPhysicalMaterial
              color="#7DCFFF"
              roughness={0.15}
              metalness={0.1}
              transparent
              opacity={0.12}
              transmission={0.45}
              depthWrite={false}
            />
          )}
        </mesh>
      ))}

      {/* converging streams */}
      {streams.map((stream, i) => (
        <Line
          key={`stream-${i}`}
          points={stream.points}
          color={stream.color}
          lineWidth={0.8}
          transparent
          opacity={0.45}
        />
      ))}
      
      {/* Combined path output */}
      <Line
        points={[new THREE.Vector3(0, 0.2, -132), new THREE.Vector3(0, 0.2, -145)]}
        color="#59F4E1"
        lineWidth={1.5}
        transparent
        opacity={0.9}
      />
    </group>
  );
}

// Chapter 4: SHAP Tunnel
function ShapTunnel() {
  const branches = useMemo(() => {
    const zStart = -145;
    const zEnd = -180;
    const count = 10;
    const arr = [];
    for (let i = 0; i < count; i++) {
      const z = zStart - (i / count) * (zStart - zEnd);
      const isPositive = i % 2 === 0;
      const color = isPositive ? "#59F4E1" : "#FF6B72";
      const dir = isPositive ? 1 : -1;
      
      const start = new THREE.Vector3(0, 0.2, z);
      const middle = new THREE.Vector3(dir * 1.6, 0.4, z - 2);
      const end = new THREE.Vector3(dir * 3.4, 0.1, z - 4.5);
      
      const curve = new THREE.QuadraticBezierCurve3(start, middle, end);
      arr.push({ points: curve.getPoints(16), color });
    }
    return arr;
  }, []);

  return (
    <group>
      {branches.map((branch, i) => (
        <Line
          key={`shap-${i}`}
          points={branch.points}
          color={branch.color}
          lineWidth={1.1}
          transparent
          opacity={0.65}
        />
      ))}
    </group>
  );
}

// Chapter 5: Access Chamber Score Arc
function AccessChamber({ progress }) {
  const reveal = THREE.MathUtils.smoothstep(progress, 0.82, 0.96);
  const groupRef = useRef(null);

  useFrame((state) => {
    if (!groupRef.current) return;
    const time = state.clock.getElapsedTime();
    groupRef.current.rotation.z = Math.sin(time * 0.15) * 0.04;
  });

  return (
    <group ref={groupRef} position={[0, 0, -226]} scale={1.25 + reveal * 0.25}>
      {/* Score gauge arcs */}
      {[2.1, 2.3, 2.5].map((radius, idx) => (
        <mesh key={idx} rotation={[0, 0, Math.PI * 0.9]}>
          <torusGeometry args={[radius, 0.012 + idx * 0.004, 6, 64, Math.PI * 1.2]} />
          <meshBasicMaterial
            color={idx === 2 ? "#D7B86F" : idx === 1 ? "#7DCFFF" : "#59F4E1"}
            transparent
            opacity={(0.12 + idx * 0.14) * reveal}
            blending={THREE.AdditiveBlending}
          />
        </mesh>
      ))}

      {/* Ticks */}
      {Array.from({ length: 11 }, (_, i) => {
        const angle = Math.PI * 0.9 + (i / 10) * (Math.PI * 1.2);
        const r = 2.3;
        const x = Math.cos(angle) * r;
        const y = Math.sin(angle) * r;
        return (
          <mesh key={i} position={[x, y, 0]} rotation={[0, 0, angle]}>
            <boxGeometry args={[0.12, 0.02, 0.02]} />
            <meshBasicMaterial color="#59F4E1" transparent opacity={0.15 + reveal * 0.65} />
          </mesh>
        );
      })}
    </group>
  );
}

export default function SignalWorld() {
  const { chapterProgress, qualityTier } = useVisualExperience();
  const count = Math.max(qualityTier.name === "mobile" ? 250 : qualityTier.particleCount, 250);
  const reducedMotion = qualityTier.reducedMotion;

  return (
    <>
      <color attach="background" args={["#02050B"]} />
      <fog attach="fog" args={["#02050B", 10, 68]} />
      <ambientLight intensity={0.16} />
      
      {/* Lighting points */}
      <pointLight position={[0, 1.5, -8]} color="#59F4E1" intensity={1.5} distance={18} />
      <pointLight position={[2, -0.6, -42]} color="#D7B86F" intensity={0.9} distance={15} />
      <pointLight position={[-1.5, 0.8, -120]} color="#7DCFFF" intensity={1.2} distance={20} />

      <SpaceParticles count={count} reducedMotion={reducedMotion} />
      <CorridorRails reducedMotion={reducedMotion} />
      
      {/* Chapter specific worlds */}
      <CorridorCorridor qualityTier={qualityTier} />
      <BehavioralNodes qualityTier={qualityTier} />
      <ModelEnsemble qualityTier={qualityTier} />
      <ShapTunnel />
      <AccessChamber progress={chapterProgress} />

      <CameraRig progress={chapterProgress} reducedMotion={reducedMotion} />
    </>
  );
}
