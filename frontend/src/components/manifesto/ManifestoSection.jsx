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
      gsap.set(lines, { autoAlpha: 0, y: 50, x: 0, scale: 1 });
      gsap.set(lines[0], { x: -70 });
      gsap.set(lines[1], { x: 70 });
      gsap.set(lines[2], { scale: 0.86 });

      const timeline = gsap.timeline({
        scrollTrigger: {
          trigger: sectionRef.current,
          start: "top top",
          end: "+=200%",
          pin: true,
          scrub: 1,
        },
      });

      timeline
        .to(progressRef.current, { scaleY: 1, transformOrigin: "top", ease: "none" }, 0)
        .to(lines[0], { autoAlpha: 1, x: 0, y: 0, duration: 0.25 }, 0.03)
        .to(lines[0], { color: "var(--text-muted)", duration: 0.18 }, 0.34)
        .to(lines[1], { autoAlpha: 1, x: 0, y: 0, duration: 0.25 }, 0.34)
        .to(lines[1], { color: "var(--text-muted)", duration: 0.18 }, 0.66)
        .to(lines[2], { autoAlpha: 1, y: 0, scale: 1, duration: 0.28 }, 0.66);
    }, sectionRef);

    return () => context.revert();
  }, []);

  return (
    <section id="manifesto" ref={sectionRef} className="manifesto-section" data-section>
      <div className="manifesto-progress">
        <span ref={progressRef} />
      </div>
      <div className="manifesto-copy">
        <h2 className="manifesto-line">Traditional credit scores ignore 89% of your financial story.</h2>
        <h2 className="manifesto-line">They don't see how you think. How you plan. How resilient you are.</h2>
        <h2 className="manifesto-line manifesto-line--gradient">AlterScore sees the whole picture.</h2>
      </div>
    </section>
  );
}
