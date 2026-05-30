import { useEffect, useRef } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

const pillars = [
  {
    title: "Assessment",
    description:
      "A focused sequence covering numeracy, financial judgement, risk preference, resilience, and social context.",
    type: "dots",
  },
  {
    title: "Behavior",
    description:
      "Response rhythm, answer changes, session duration, typing cadence, and hesitation become quiet context.",
    type: "wave",
  },
  {
    title: "Explanation",
    description:
      "Every score returns factors, eligibility, and actions that can move the borrower upward.",
    type: "graph",
  },
];

function Icon({ type }) {
  if (type === "wave") {
    return (
      <svg className="pillar-icon" viewBox="0 0 80 80" aria-hidden="true">
        <path d="M8 42 C 20 18, 30 18, 42 42 S 64 66, 74 42" />
        <path d="M8 50 C 20 30, 30 30, 42 50 S 64 70, 74 50" />
        <path d="M8 34 C 20 10, 30 10, 42 34 S 64 58, 74 34" />
      </svg>
    );
  }

  if (type === "graph") {
    const nodes = [[18, 20], [58, 18], [66, 52], [38, 62], [12, 48], [40, 36]];
    return (
      <svg className="pillar-icon" viewBox="0 0 80 80" aria-hidden="true">
        {nodes.slice(0, 5).map(([x, y], index) => (
          <line key={index} x1={x} y1={y} x2="40" y2="36" />
        ))}
        {nodes.map(([x, y], index) => (
          <circle key={`${x}-${y}`} cx={x} cy={y} r={index === 5 ? 6 : 4} />
        ))}
      </svg>
    );
  }

  return (
    <svg className="pillar-icon pillar-icon--dots" viewBox="0 0 80 80" aria-hidden="true">
      {Array.from({ length: 25 }, (_, index) => {
        const x = 16 + (index % 5) * 12;
        const y = 16 + Math.floor(index / 5) * 12;
        return <circle key={index} cx={x} cy={y} r="2.6" className={index < 22 ? "is-lit" : ""} />;
      })}
    </svg>
  );
}

function handleMove(event) {
  const rect = event.currentTarget.getBoundingClientRect();
  event.currentTarget.style.setProperty("--mx", `${event.clientX - rect.left}px`);
  event.currentTarget.style.setProperty("--my", `${event.clientY - rect.top}px`);
}

export default function PillarsSection() {
  const containerRef = useRef(null);
  const labelRef = useRef(null);

  useEffect(() => {
    let mm = gsap.matchMedia();

    // 1. Desktop Timeline (with Pinning)
    mm.add("(min-width: 981px)", () => {
      const cards = gsap.utils.toArray(".pillar-card");

      // 1. Initial layout states
      gsap.set(labelRef.current, { autoAlpha: 0, y: -20 });
      gsap.set(cards, { autoAlpha: 0, y: 120, rotateX: 12, filter: "blur(10px)" });

      // 2. Scroll-Pinned Scrub Sequence
      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: containerRef.current,
          start: "top top",
          end: "+=120%",
          pin: true,
          scrub: 1.2,
          pinSpacing: true,
        }
      });

      // Sequence timeline choreography
      tl.to(labelRef.current, { autoAlpha: 1, y: 0, duration: 0.15 })
        
        // Card 1
        .to(cards[0], { autoAlpha: 1, y: 0, rotateX: 0, filter: "blur(0px)", duration: 0.3 }, 0.15)
        
        // Card 2
        .to(cards[1], { autoAlpha: 1, y: 0, rotateX: 0, filter: "blur(0px)", duration: 0.3 }, 0.45)
        
        // Card 3
        .to(cards[2], { autoAlpha: 1, y: 0, rotateX: 0, filter: "blur(0px)", duration: 0.3 }, 0.75)
        
        // Final glow state: slightly brighten all borders
        .to(cards, {
          borderColor: "rgba(212, 168, 83, 0.28)",
          duration: 0.15,
        }, 1.05);
    });

    // 2. Mobile/Tablet Timeline (Fluid scrolling, No Pinning)
    mm.add("(max-width: 980px)", () => {
      const cards = gsap.utils.toArray(".pillar-card");

      gsap.set(labelRef.current, { autoAlpha: 0, y: -15 });
      gsap.set(cards, { autoAlpha: 0, y: 40, filter: "blur(6px)" });

      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: containerRef.current,
          start: "top 75%",
          end: "bottom bottom",
          scrub: false,
        }
      });

      tl.to(labelRef.current, { autoAlpha: 1, y: 0, duration: 0.4 })
        .to(cards, {
          autoAlpha: 1,
          y: 0,
          filter: "blur(0px)",
          stagger: 0.2,
          duration: 0.65,
          ease: "power2.out"
        }, "-=0.2")
        .to(cards, {
          borderColor: "rgba(212, 168, 83, 0.28)",
          duration: 0.4,
        });
    });

    return () => mm.revert();
  }, []);

  return (
    <section ref={containerRef} className="pillars-section" data-section>
      <p ref={labelRef} className="section-label">What it measures</p>
      <div className="pillar-grid">
        {pillars.map((pillar, index) => (
          <article
            className="pillar-card"
            key={pillar.title}
            onMouseMove={handleMove}
            style={{ "--stagger": `${index * 100}ms` }}
            data-cursor="interactive"
          >
            <Icon type={pillar.type} />
            <h3>{pillar.title}</h3>
            <p>{pillar.description}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
