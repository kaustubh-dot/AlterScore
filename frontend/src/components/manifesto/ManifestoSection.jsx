import { useEffect, useRef } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

export default function ManifestoSection() {
  const sectionRef = useRef(null);
  const progressRef = useRef(null);

  useEffect(() => {
    const context = gsap.context(() => {
      const lines = gsap.utils.toArray(".manifesto-line");
      
      // 1. Initial State: massive y shift, strong blur, alternating x-offset
      gsap.set(lines[0], { autoAlpha: 0, y: 80, x: -30, scale: 0.92, filter: "blur(12px)" });
      gsap.set(lines[1], { autoAlpha: 0, y: 80, x: 30, scale: 0.92, filter: "blur(12px)" });
      gsap.set(lines[2], { autoAlpha: 0, y: 80, x: 0, scale: 0.92, filter: "blur(12px)" });

      const timeline = gsap.timeline({
        scrollTrigger: {
          trigger: sectionRef.current,
          start: "top top",
          end: "+=150%",
          pin: true,
          scrub: 1.2,
        },
      });

      // 2. Slow, rich scroll animations
      timeline
        // Progress bar scales and glows
        .to(progressRef.current, { 
          scaleY: 1, 
          transformOrigin: "top", 
          boxShadow: "0 0 15px rgba(212, 168, 83, 0.6)",
          ease: "none" 
        }, 0)
        
        // Line 1 Reveal
        .to(lines[0], { autoAlpha: 1, y: 0, x: 0, scale: 1, filter: "blur(0px)", duration: 0.4 }, 0.05)
        .to(lines[0], { color: "var(--text-muted)", duration: 0.3 }, 0.42)
        
        // Line 2 Reveal
        .to(lines[1], { autoAlpha: 1, y: 0, x: 0, scale: 1, filter: "blur(0px)", duration: 0.4 }, 0.42)
        .to(lines[1], { color: "var(--text-muted)", duration: 0.3 }, 0.78)
        
        // Line 3 Reveal (Gradient final payoff)
        .to(lines[2], { autoAlpha: 1, y: 0, x: 0, scale: 1, filter: "blur(0px)", duration: 0.45 }, 0.78);

    }, sectionRef);

    return () => context.revert();
  }, []);

  return (
    <section id="manifesto" ref={sectionRef} className="manifesto-section" data-section>
      <div className="manifesto-progress">
        <span ref={progressRef} style={{ display: "block", width: "100%", height: "100%" }} />
      </div>
      <div className="manifesto-copy">
        <h2 className="manifesto-line">A score should not feel like a locked door.</h2>
        <h2 className="manifesto-line">It should reveal the signals behind the decision.</h2>
        <h2 className="manifesto-line manifesto-line--gradient">AlterScore makes credit feel legible.</h2>
      </div>
    </section>
  );
}
