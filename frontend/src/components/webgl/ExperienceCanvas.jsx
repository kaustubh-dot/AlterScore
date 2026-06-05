import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { Bloom, EffectComposer } from "@react-three/postprocessing";
import { Suspense, useCallback, useEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";

import { useVisualExperience } from "../../context/VisualExperienceContext.jsx";
import CreditSignalCore from "./CreditSignalCore.jsx";
import SignalWorld from "./SignalWorld.jsx";

function CameraRig({ mode, progress, reducedMotion }) {
  const { camera } = useThree();
  const pointer = useRef({ x: 0, y: 0 });

  useFrame((state) => {
    pointer.current.x = THREE.MathUtils.lerp(pointer.current.x, state.pointer.x, 0.035);
    pointer.current.y = THREE.MathUtils.lerp(pointer.current.y, state.pointer.y, 0.035);

    const assessment = mode === "assessment" || mode === "processing";
    const result = mode === "results";
    const targetX = assessment ? 2.75 : result ? 0 : THREE.MathUtils.lerp(2.1, -1.7, progress);
    const targetY = assessment ? 0.35 : result ? 0.42 : THREE.MathUtils.lerp(0.45, -0.12, progress);
    const targetZ = assessment ? 7.3 : result ? 7 : THREE.MathUtils.lerp(6.6, 5.35, progress);

    camera.position.x = THREE.MathUtils.lerp(
      camera.position.x,
      targetX + (reducedMotion ? 0 : pointer.current.x * 0.16),
      0.045,
    );
    camera.position.y = THREE.MathUtils.lerp(
      camera.position.y,
      targetY + (reducedMotion ? 0 : pointer.current.y * 0.1),
      0.045,
    );
    camera.position.z = THREE.MathUtils.lerp(camera.position.z, targetZ, 0.045);
    camera.lookAt(assessment ? 1.5 : 0, assessment ? 0.1 : -0.1, 0);
  });

  return null;
}

function ParticleField({ count, mode, reducedMotion }) {
  const ref = useRef(null);
  const positions = useMemo(() => {
    const values = new Float32Array(count * 3);
    for (let index = 0; index < count; index += 1) {
      values[index * 3] = (Math.random() - 0.5) * 20;
      values[index * 3 + 1] = (Math.random() - 0.5) * 10;
      values[index * 3 + 2] = -2 - Math.random() * 10;
    }
    return values;
  }, [count]);

  useFrame((_, delta) => {
    if (!ref.current || reducedMotion) return;
    ref.current.rotation.y += delta * (mode === "processing" ? 0.028 : 0.009);
  });

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <pointsMaterial
        color="#79dcff"
        opacity={mode === "assessment" ? 0.12 : 0.24}
        size={0.018}
        sizeAttenuation
        transparent
      />
    </points>
  );
}

function DataTerrain({ segments, mode }) {
  return (
    <mesh position={[0, -2.1, -3.2]} rotation={[-Math.PI / 2, 0, 0]}>
      <planeGeometry args={[24, 18, segments, segments]} />
      <meshBasicMaterial
        color="#49d9ee"
        opacity={mode === "assessment" ? 0.025 : 0.075}
        transparent
        wireframe
      />
    </mesh>
  );
}

function World() {
  const { chapterProgress, mode, processingIntensity, qualityTier, scoreTarget } = useVisualExperience();
  if (mode === "landing") return <SignalWorld />;

  return (
    <>
      <ambientLight intensity={0.22} />
      <ParticleField count={qualityTier.particleCount} mode={mode} reducedMotion={qualityTier.reducedMotion} />
      <DataTerrain segments={qualityTier.terrainSegments} mode={mode} />
      <CreditSignalCore
        mode={mode}
        progress={chapterProgress}
        processingIntensity={processingIntensity}
        reducedMotion={qualityTier.reducedMotion}
        scoreTarget={scoreTarget}
      />
      <CameraRig mode={mode} progress={chapterProgress} reducedMotion={qualityTier.reducedMotion} />
      {qualityTier.bloom && (
        <EffectComposer multisampling={0}>
          <Bloom threshold={0.38} strength={mode === "assessment" ? 0.28 : 0.62} radius={0.72} />
        </EffectComposer>
      )}
    </>
  );
}

const UNITY_SCALE = 100000;

function getUnityBuildCandidate() {
  const isMobile = /Mobile|iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
  const envBase = import.meta.env?.VITE_UNITY_BUILD_BASE_URL;
  const envDesktop = import.meta.env?.VITE_UNITY_BUILD_NAME_DESKTOP;
  const envMobile = import.meta.env?.VITE_UNITY_BUILD_NAME_MOBILE;

  if (envBase && (envDesktop || envMobile)) {
    return {
      baseUrl: envBase.replace(/\/$/, ""),
      buildName: isMobile ? envMobile || envDesktop : envDesktop || envMobile,
      source: "licensed",
    };
  }

  return {
    baseUrl: "/Build",
    buildName: isMobile ? "Sidewave_WebGL_260421_astc" : "Sidewave_WebGL_260421_dxt",
    source: "local",
  };
}

function unityAssetUrl(candidate, extension) {
  return `${candidate.baseUrl}/${candidate.buildName}.${extension}`;
}

async function assertUnityAsset(url) {
  const response = await fetch(url, { method: "HEAD", cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Unity asset unavailable: ${url}`);
  }
}

function loadScript(src, id) {
  return new Promise((resolve, reject) => {
    if (document.getElementById(id)) {
      resolve();
      return;
    }
    const script = document.createElement("script");
    script.src = src;
    script.id = id;
    script.async = false;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error(`Failed to load script ${src}`));
    document.body.appendChild(script);
  });
}

function UnityLandingCanvas() {
  const { qualityTier } = useVisualExperience();
  const [status, setStatus] = useState("booting");
  const [progress, setProgress] = useState(0);
  const instanceRef = useRef(null);
  const timedOutRef = useRef(false);
  const scrollRef = useRef({ current: 0, target: 0, last: -1, lastTime: performance.now() });

  const enterFallback = useCallback((reason) => {
    console.warn("Unity landing fallback:", reason);
    setStatus("fallback");
    window.dispatchEvent(new CustomEvent("alterscore:unity-status", { detail: { status: "fallback", reason } }));
  }, []);

  useEffect(() => {
    let active = true;
    let timeoutId = 0;
    const candidate = getUnityBuildCandidate();
    document.body.classList.add("mode-landing");

    window.EventDispatcher = (eventName) => {
      window.dispatchEvent(new CustomEvent(`unity:${eventName}`));
    };
    window.EventDispatcherWithArgument = (eventName, argument) => {
      window.dispatchEvent(new CustomEvent(`unity:${eventName}`, { detail: argument }));
      if (eventName === "TimelineLength") {
        window.dispatchEvent(new CustomEvent("alterscore:unity-timeline", { detail: argument }));
      }
      if (eventName === "WebGLSafeDraw" || eventName === "SceneReady") {
        setStatus("ready");
        window.dispatchEvent(new CustomEvent("alterscore:unity-status", { detail: { status: "ready" } }));
      }
    };

    async function bootUnity() {
      try {
        await Promise.all([
          assertUnityAsset(unityAssetUrl(candidate, "loader.js")),
          assertUnityAsset(unityAssetUrl(candidate, "framework.js")),
          assertUnityAsset(unityAssetUrl(candidate, "data.br")),
          assertUnityAsset(unityAssetUrl(candidate, "wasm.br")),
        ]);

        if (!active) return;

        const loaderId = `unity-loader-${candidate.buildName}`;
        await loadScript(unityAssetUrl(candidate, "loader.js"), loaderId);

        if (!active || typeof window.createUnityInstance !== "function") {
          throw new Error("Unity loader did not expose createUnityInstance.");
        }

        const canvas = document.getElementById("webContainer");
        const config = {
          dataUrl: unityAssetUrl(candidate, "data.br"),
          frameworkUrl: unityAssetUrl(candidate, "framework.js"),
          codeUrl: unityAssetUrl(candidate, "wasm.br"),
          streamingAssetsUrl: `${candidate.baseUrl}/StreamingAssets`,
          companyName: "AlterScore",
          productName: "AlterScore Borrower Experience",
          productVersion: "1.0.0",
        };

        timeoutId = window.setTimeout(() => {
          timedOutRef.current = true;
          if (active && !instanceRef.current) {
            enterFallback("Unity scene did not become ready before timeout.");
          }
        }, 5000);

        const unityInstance = await window.createUnityInstance(canvas, config, (value) => {
          if (!active) return;
          setProgress(Math.round(value * 100));
          window.dispatchEvent(
            new CustomEvent("alterscore:unity-status", {
              detail: { status: "loading", progress: Math.round(value * 100), source: candidate.source },
            }),
          );
        });

        if (!active || timedOutRef.current) {
          unityInstance.Quit?.();
          return;
        }

        instanceRef.current = unityInstance;
        window.clearTimeout(timeoutId);
        window.gameInstance = unityInstance;
        setProgress(100);
        setStatus("ready");
        window.dispatchEvent(new CustomEvent("alterscore:unity-status", { detail: { status: "ready", source: candidate.source } }));

        if (unityInstance.Module?.SystemInfo?.mobile) {
          unityInstance.SendMessage?.("zController", "DisableFluidFx");
        } else {
          unityInstance.SendMessage?.("zController", "EnableFluidFx");
        }
      } catch (e) {
        if (active) enterFallback(e.message || "Unity scene failed to load.");
      }
    }

    bootUnity();

    return () => {
      active = false;
      window.clearTimeout(timeoutId);

      document.documentElement.classList.remove("no-scroll");
      document.body.classList.remove("no-scroll", "isMobile", "mode-landing");
      document.body.style.overflow = "";

      if (instanceRef.current && typeof instanceRef.current.Quit === "function") {
        try {
          instanceRef.current.Quit();
        } catch (e) {
          console.warn("Error quitting Unity instance:", e);
        }
      }
      instanceRef.current = null;
      window.gameInstance = null;

      const loaderScripts = document.querySelectorAll('script[src*=".loader.js"]');
      loaderScripts.forEach(s => s.remove());
      delete window.EventDispatcher;
      delete window.EventDispatcherWithArgument;
    };
  }, [enterFallback]);

  useEffect(() => {
    let frameId = 0;

    function updateScroll(now) {
      const state = scrollRef.current;
      const total = Math.max(document.documentElement.scrollHeight - window.innerHeight, 1);
      state.target = Math.min(Math.max(window.scrollY / total, 0), 1);
      const dt = Math.min((now - state.lastTime) / 1000, 0.064);
      state.lastTime = now;
      const alpha = 1 - Math.exp(-dt / 0.46);
      state.current += (state.target - state.current) * alpha;

      if (instanceRef.current && Math.abs(state.current - state.last) > 0.0004) {
        state.last = state.current;
        try {
          instanceRef.current.SendMessage("Timeline", "SetScrollValue", Math.round(state.current * UNITY_SCALE));
        } catch {
          // Unity scenes vary by export; absence of Timeline should not break React.
        }
      }

      frameId = window.requestAnimationFrame(updateScroll);
    }

    frameId = window.requestAnimationFrame(updateScroll);
    return () => window.cancelAnimationFrame(frameId);
  }, []);

  const showFallback = status === "fallback";
  const ready = status === "ready";

  return (
    <div className={`unity-stage unity-stage--${status}`} aria-hidden="true">
      <div className="unity-stage__shade" />
      <div id="unityContainer" className="webgl-content unity-desktop">
        <canvas id="webContainer" className={ready ? "is-visible" : ""} />
      </div>

      {showFallback && (
        <Canvas
          className="unity-fallback-canvas"
          camera={{ position: [0, 0, 50], fov: 48, near: 0.1, far: 320 }}
          dpr={qualityTier.dpr}
          gl={{
            antialias: qualityTier.name !== "mobile",
            alpha: true,
            powerPreference: "high-performance",
            stencil: false,
          }}
        >
          <Suspense fallback={null}>
            <World />
          </Suspense>
        </Canvas>
      )}

      {status === "booting" && (
        <div className="unity-stage__boot">
          <span>{String(progress).padStart(3, "0")}</span>
          <i style={{ transform: `scaleX(${progress / 100})` }} />
        </div>
      )}
    </div>
  );
}

export default function ExperienceCanvas() {
  const { mode, qualityTier } = useVisualExperience();
  if (mode === "dashboard") return <div className="experience-backdrop experience-backdrop--dashboard" />;
  if (mode === "landing") return <UnityLandingCanvas />;

  return (
    <div className={`experience-world experience-world--${mode}`} aria-hidden="true">
      <div className="experience-backdrop" />
      <div className="experience-backdrop-shade" />
      <Canvas
        camera={{ position: [0.8, 0.35, 9], fov: mode === "landing" ? 48 : 42, near: 0.1, far: mode === "landing" ? 95 : 40 }}
        dpr={qualityTier.dpr}
        gl={{
          antialias: qualityTier.name !== "mobile",
          alpha: true,
          powerPreference: "high-performance",
          stencil: false,
        }}
      >
        <Suspense fallback={null}>
          <World />
        </Suspense>
      </Canvas>
    </div>
  );
}
