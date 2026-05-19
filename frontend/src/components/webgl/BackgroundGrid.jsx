import { useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import * as THREE from "three";

const vertexShader = `
  varying vec2 vUv;

  void main() {
    vUv = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

const fragmentShader = `
  varying vec2 vUv;
  uniform float uTime;

  float grid(vec2 uv) {
    vec2 coord = fract(uv * 80.0);
    vec2 line = smoothstep(vec2(0.015), vec2(0.0), min(coord, 1.0 - coord));
    return max(line.x, line.y);
  }

  void main() {
    vec2 centered = vUv - 0.5;
    float fade = smoothstep(0.72, 0.18, length(centered));
    float scan = 0.5 + 0.5 * sin((vUv.y + uTime * 0.025) * 80.0);
    float lines = grid(vUv);
    vec3 color = vec3(0.239, 1.0, 0.784);
    gl_FragColor = vec4(color, lines * fade * (0.035 + scan * 0.035));
  }
`;

export default function BackgroundGrid() {
  const materialRef = useRef(null);
  const uniforms = useMemo(() => ({ uTime: { value: 0 } }), []);

  useFrame((state) => {
    if (materialRef.current) materialRef.current.uniforms.uTime.value = state.clock.elapsedTime;
  });

  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -2.65, -4.6]}>
      <planeGeometry args={[100, 100, 80, 80]} />
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
    </mesh>
  );
}
