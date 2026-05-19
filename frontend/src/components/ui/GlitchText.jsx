import { useEffect, useRef, useState } from "react";

const SCRAMBLE_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%&*<>/\\";

export default function GlitchText({
  text,
  as: Component = "span",
  className = "",
  delay = 0,
  trigger = "mount",
}) {
  const frameRef = useRef(0);
  const intervalRef = useRef(0);
  const [displayText, setDisplayText] = useState(text);

  const scramble = () => {
    if (frameRef.current > 0 && frameRef.current < 30) return;
    window.clearInterval(intervalRef.current);
    frameRef.current = 0;
    const target = String(text || "");
    const maxFrames = Math.max(12, Math.min(30, target.length + 7));

    intervalRef.current = window.setInterval(() => {
      frameRef.current += 1;
      const settled = Math.floor((frameRef.current / maxFrames) * target.length);

      const next = target
        .split("")
        .map((char, index) => {
          if (char === " ") return " ";
          if (index < settled) return char;
          return SCRAMBLE_CHARS[Math.floor(Math.random() * SCRAMBLE_CHARS.length)];
        })
        .join("");

      setDisplayText(next);

      if (frameRef.current >= maxFrames) {
        window.clearInterval(intervalRef.current);
        setDisplayText(target);
        frameRef.current = 0;
      }
    }, 24);
  };

  useEffect(() => {
    setDisplayText(text);
    if (trigger === "mount") {
      const timeout = window.setTimeout(scramble, delay * 1000);
      return () => {
        window.clearTimeout(timeout);
        window.clearInterval(intervalRef.current);
      };
    }

    return () => window.clearInterval(intervalRef.current);
  }, [text, delay, trigger]);

  return (
    <Component
      className={`scramble-text ${className}`}
      onMouseEnter={scramble}
      onFocus={scramble}
      tabIndex={trigger === "hover" ? 0 : undefined}
    >
      {displayText}
    </Component>
  );
}
