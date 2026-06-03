import { useEffect, useState, useRef } from "react";

const SYMBOLS = "!<>-_\\/[]{}=+*^?#@$%&";

export default function ScrambleText({ text, visible }) {
  const [displayText, setDisplayText] = useState("");
  const frameRef = useRef(null);

  useEffect(() => {
    if (!visible) {
      setDisplayText("");
      return;
    }

    const duration = 800;
    const startTime = Date.now();

    const updateText = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const revealCount = Math.floor(progress * text.length);

      let current = "";
      for (let i = 0; i < text.length; i++) {
        if (i < revealCount) {
          current += text[i];
        } else if (text[i] === " ") {
          current += " ";
        } else {
          const randChar = SYMBOLS[Math.floor(Math.random() * SYMBOLS.length)];
          current += randChar;
        }
      }

      setDisplayText(current);

      if (progress < 1) {
        frameRef.current = requestAnimationFrame(updateText);
      } else {
        setDisplayText(text);
      }
    };

    frameRef.current = requestAnimationFrame(updateText);

    return () => {
      if (frameRef.current) cancelAnimationFrame(frameRef.current);
    };
  }, [text, visible]);

  return <span className="scramble-text">{displayText}</span>;
}
