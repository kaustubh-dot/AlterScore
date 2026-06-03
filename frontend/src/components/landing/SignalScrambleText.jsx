import { useEffect, useState } from "react";

const CHARACTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";

export default function SignalScrambleText({ text, active = true }) {
  const [output, setOutput] = useState(text);

  useEffect(() => {
    if (!active) {
      setOutput(text);
      return undefined;
    }

    let frame = 0;
    const totalFrames = Math.max(18, text.length * 2);
    const timer = window.setInterval(() => {
      frame += 1;
      const resolved = Math.floor((frame / totalFrames) * text.length);
      setOutput(
        text
          .split("")
          .map((character, index) => {
            if (character === " " || index < resolved) return character;
            return CHARACTERS[Math.floor(Math.random() * CHARACTERS.length)];
          })
          .join(""),
      );

      if (frame >= totalFrames) {
        window.clearInterval(timer);
        setOutput(text);
      }
    }, 26);

    return () => window.clearInterval(timer);
  }, [active, text]);

  return output;
}
