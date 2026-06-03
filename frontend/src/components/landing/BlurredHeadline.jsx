import { useEffect, useRef } from "react";
import { gsap } from "gsap";

export default function BlurredHeadline({ text, visible }) {
  const containerRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const words = containerRef.current.querySelectorAll(".word");
    if (visible) {
      gsap.to(words, {
        opacity: 1,
        filter: "blur(0px)",
        y: 0,
        stagger: 0.15, // Stagger word entry
        duration: 1.2,
        ease: "power2.out",
        overwrite: "auto",
      });
    } else {
      gsap.to(words, {
        opacity: 0,
        filter: "blur(20px)",
        y: 10,
        duration: 0.5,
        ease: "power2.in",
        overwrite: "auto",
      });
    }
  }, [visible, text]);

  const wordsList = text.split(" ");

  return (
    <h2 ref={containerRef} className="blurred-headline">
      {wordsList.map((word, idx) => (
        <span
          key={idx}
          className="word"
          style={{
            display: "inline-block",
            opacity: 0,
            filter: "blur(20px)",
            transform: "translateY(10px)",
            marginRight: "0.28em",
            whiteSpace: "nowrap",
          }}
        >
          {word}
        </span>
      ))}
    </h2>
  );
}

