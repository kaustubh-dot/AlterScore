import { useEffect, useState, useRef } from "react";
import { gsap } from "gsap";

const CHARS = "!<>-_\\\\/[]{}—=+*^?#_";

function GlitchChar({ char }) {
  const [display, setDisplay] = useState(char);
  const iters = useRef(0);

  useEffect(() => {
    if (char === " " || char === "[" || char === "]") return;
    const interval = setInterval(() => {
      if (iters.current > 15) {
        clearInterval(interval);
        setDisplay(char);
      } else {
        setDisplay(CHARS[Math.floor(Math.random() * CHARS.length)]);
      }
      iters.current += 1;
    }, 30);
    return () => clearInterval(interval);
  }, [char]);

  return <span>{display}</span>;
}

export default function LoadingScreen({ onComplete }) {
  const [progress, setProgress] = useState(0);
  const [stage, setStage] = useState(0); // 0 = loading, 1 = ready
  const [exiting, setExiting] = useState(false);
  const loaderRef = useRef(null);

  useEffect(() => {
    let timeout;
    let current = 0;

    const tick = () => {
      current += Math.floor(Math.random() * 15) + 1;
      if (current >= 100) {
        setProgress(100);
        setStage(1);
      } else {
        setProgress(current);
        timeout = setTimeout(tick, Math.random() * 200 + 50);
      }
    };

    timeout = setTimeout(tick, 500);

    return () => clearTimeout(timeout);
  }, []);

  const handleEnter = () => {
    setExiting(true);
    gsap.to(loaderRef.current, {
      y: "-100%",
      duration: 1.2,
      ease: "power4.inOut",
      onComplete: () => {
        if (onComplete) onComplete();
      },
    });
  };

  const formattedProgress = `[${String(progress).padStart(3, "0")}%]`;
  const readyText = "[CLICK TO INITIALIZE]";

  return (
    <div 
      ref={loaderRef}
      className="kvs-loader-screen" 
      style={{
        position: "fixed",
        inset: 0,
        backgroundColor: "#000000",
        zIndex: 9999,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        color: stage === 1 ? "#FF5500" : "#ffffff",
        fontFamily: "var(--font-mono)",
        fontSize: "clamp(24px, 4vw, 40px)",
        letterSpacing: "0.1em",
        cursor: stage === 1 ? "pointer" : "default",
        userSelect: "none",
      }}
      onClick={stage === 1 ? handleEnter : undefined}
    >
      <div 
        style={{
          transition: "color 0.3s ease",
          opacity: exiting ? 0 : 1,
        }}
      >
        {stage === 0 ? (
          formattedProgress.split("").map((char, index) => (
            <GlitchChar key={index} char={char} />
          ))
        ) : (
          readyText.split("").map((char, index) => (
            <GlitchChar key={index} char={char} />
          ))
        )}
      </div>
    </div>
  );
}
