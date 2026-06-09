import React, { useEffect, useState } from 'react';

export default function GlitchText({ text, speed = 30, triggerOnMount = false }) {
  const [displayText, setDisplayText] = useState(text);
  const [isHovered, setIsHovered] = useState(false);

  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%&ΔΨΦ';

  const triggerGlitch = () => {
    let iteration = 0;
    const interval = setInterval(() => {
      setDisplayText(
        text
          .split('')
          .map((char, index) => {
            if (char === ' ') return ' ';
            if (index < iteration) return text[index];
            return chars[Math.floor(Math.random() * chars.length)];
          })
          .join('')
      );

      if (iteration >= text.length) {
        clearInterval(interval);
        setDisplayText(text);
      }
      iteration += 1 / 3;
    }, speed);
  };

  useEffect(() => {
    if (isHovered) {
      triggerGlitch();
    }
  }, [isHovered]);

  useEffect(() => {
    if (triggerOnMount) {
      triggerGlitch();
    }
  }, [text, triggerOnMount]);

  return (
    <span 
      onMouseEnter={() => setIsHovered(true)} 
      onMouseLeave={() => setIsHovered(false)}
      style={{ cursor: 'inherit', display: 'inline-block' }}
    >
      {displayText}
    </span>
  );
}
