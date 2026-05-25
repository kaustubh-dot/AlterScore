import { useEffect, useRef } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

const backgroundConfig = [
  { id: "hero", src: "/bg-hero.png", selector: ".hero-section" },
  { id: "manifesto", src: "/bg-manifesto.png", selector: ".manifesto-section" },
  { id: "pillars", src: "/bg-pillars.png", selector: ".pillars-section" },
  { id: "spec", src: "/bg-spec.png", selector: ".model-spec-section" },
  { id: "footer", src: "/bg-footer.png", selector: ".site-footer" },
];

export default function BackgroundLayer() {
  const containerRef = useRef(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      backgroundConfig.forEach((bg, index) => {
        const el = document.querySelector(bg.selector);
        const img = document.querySelector(`[data-bg-id="${bg.id}"]`);
        if (!el || !img) return;

        const maxOpacity = bg.id === "hero" ? 0.85 : 0.70;

        // Simple parallax drift — minimal yPercent range
        gsap.fromTo(
          img,
          { yPercent: -3 },
          {
            yPercent: 3,
            ease: "none",
            scrollTrigger: {
              trigger: el,
              start: "top bottom",
              end: "bottom top",
              scrub: 1.5,
            },
          }
        );

        // Symmetric dynamic cross-fade with 1.4s smooth dissolve
        ScrollTrigger.create({
          trigger: el,
          start: "top 65%",
          end: "bottom 35%",
          onEnter: () => {
            gsap.to(img, { opacity: maxOpacity, duration: 1.4, ease: "power3.inOut" });
            backgroundConfig.forEach((otherBg) => {
              if (otherBg.id !== bg.id) {
                const otherImg = document.querySelector(`[data-bg-id="${otherBg.id}"]`);
                if (otherImg) gsap.to(otherImg, { opacity: 0, duration: 1.4, ease: "power3.inOut" });
              }
            });
          },
          onEnterBack: () => {
            gsap.to(img, { opacity: maxOpacity, duration: 1.4, ease: "power3.inOut" });
            backgroundConfig.forEach((otherBg) => {
              if (otherBg.id !== bg.id) {
                const otherImg = document.querySelector(`[data-bg-id="${otherBg.id}"]`);
                if (otherImg) gsap.to(otherImg, { opacity: 0, duration: 1.4, ease: "power3.inOut" });
              }
            });
          }
        });
      });
    }, containerRef);

    return () => ctx.revert();
  }, []);

  return (
    <div ref={containerRef} className="background-layer-container">
      {backgroundConfig.map((bg, idx) => (
        <div
          key={bg.id}
          data-bg-id={bg.id}
          className="bg-layer-image"
          style={{
            backgroundImage: `url(${bg.src})`,
            position: "fixed",
            inset: 0,
            backgroundSize: "cover",
            backgroundPosition: "center",
            opacity: idx === 0 ? 0.85 : 0,
            zIndex: 0,
            pointerEvents: "none",
            transform: "scale(1.08)",
            willChange: "opacity",
            filter: "brightness(0.45) contrast(1.15) saturate(1.1)",
          }}
        />
      ))}
      <div
        className="bg-layer-vignette"
        style={{
          position: "fixed",
          inset: 0,
          background: "radial-gradient(ellipse at center, transparent 30%, rgba(8, 12, 24, 0.85) 80%)",
          zIndex: 1,
          pointerEvents: "none",
        }}
      />
    </div>
  );
}
