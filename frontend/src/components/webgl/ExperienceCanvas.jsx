import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { Bloom, EffectComposer } from "@react-three/postprocessing";
import { Suspense, useMemo, useRef, useEffect } from "react";
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

function loadOptionalScript(src, id) {
  return loadScript(src, id).catch((e) => {
    console.warn(`Optional script failed to load: ${src}`, e);
  });
}

function UnityContainer() {
  useEffect(() => {
    let isMounted = true;
    document.body.classList.add("mode-landing");

    const loadAll = async () => {
      try {
        await loadScript("/js/jquery.min.js", "jquery-script");
        await loadScript("/js/jquery.easing.min.js", "jquery-easing-script");
        
        if (!isMounted) return;

        await loadOptionalScript("/js/cookieconsent.umd.js?ver=1.63", "cookieconsent-script");
        await loadOptionalScript("/js/cookie.js?ver=1.63", "cookie-script");
        await loadScript("/js/unity-loader.js?ver=1.63", "unity-loader-script");
        await loadOptionalScript("/js/translator.js?ver=1.63", "translator-script");
        await loadOptionalScript("/js/lemon.js", "lemon-script");
        await loadOptionalScript("/js/ai-chat.js?ver=1.63", "ai-chat-script");
        await loadScript("/js/ui-interactions.js?ver=1.63", "ui-interactions-script");
        await loadScript("/js/scroll-navigation.js?ver=1.63", "scroll-navigation-script");
        await loadScript("/js/scroll-visuals.js?ver=1.63", "scroll-visuals-script");
      } catch (e) {
        console.error("Error loading Unity scripts:", e);
      }
    };

    loadAll();

    return () => {
      isMounted = false;

      // Reset document classes and scroll states
      document.documentElement.classList.remove("no-scroll");
      document.body.classList.remove("no-scroll", "isMobile", "mode-landing");
      document.body.style.overflow = "";

      // Cleanup global event listeners namespaced with .landing
      if (window.jQuery) {
        window.jQuery(window).off(".landing");
        window.jQuery(document).off(".landing");
      }

      // Clean up native wheel and touch event listeners
      if (window.landingHandlers) {
        window.removeEventListener("wheel", window.landingHandlers.wheel, { passive: false });
        window.removeEventListener("touchstart", window.landingHandlers.touchstart, { passive: true });
        window.removeEventListener("touchmove", window.landingHandlers.touchmove, { passive: false });
        window.removeEventListener("touchend", window.landingHandlers.touchend, { passive: true });
        delete window.landingHandlers;
      }

      // Quit Unity instance to free WebGL memory
      if (window.gameInstance && typeof window.gameInstance.Quit === "function") {
        try {
          window.gameInstance.Quit();
        } catch (e) {
          console.warn("Error quitting Unity instance:", e);
        }
        window.gameInstance = null;
      }

      // Remove script tags from DOM (excluding jQuery to avoid event dispatcher corruption)
      [
        "cookieconsent-script",
        "cookie-script",
        "translator-script",
        "ai-chat-script",
        "unity-loader-script",
        "ui-interactions-script",
        "scroll-navigation-script",
        "scroll-visuals-script"
      ].forEach((id) => {
        const el = document.getElementById(id);
        if (el) el.remove();
      });

      // Remove any loaded build script appended by unity-loader
      const loaderScripts = document.querySelectorAll('script[src*=".loader.js"]');
      loaderScripts.forEach(s => s.remove());
    };
  }, []);

  return (
    <div id="unityContainer" className="webgl-content unity-desktop">
      <div id="unityProgress" className="progress">
        <div className="empty"></div>
        <div id="unity-progress-bar-full" className="full"></div>
      </div>
      <div id="loadingMessages" className="hideAfterLoading"><span></span></div>
      <canvas id="webContainer"></canvas>
    </div>
  );
}

export default function ExperienceCanvas() {
  const { mode, qualityTier } = useVisualExperience();
  if (mode === "dashboard") return <div className="experience-backdrop experience-backdrop--dashboard" />;
  if (mode === "landing") return <UnityContainer />;

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
