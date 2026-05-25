import { useEffect, useRef } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

const rows = [
  ["Runtime", "Calibrated stacking ensemble"],
  ["Base estimators", "6"],
  ["Score range", "300 - 850"],
  ["Explainability", "SHAP attributions"],
  ["Action engine", "DICE recourse paths"],
  ["Submission", "Retry-safe state payload"],
];

export default function ModelSpecSection() {
  const sectionRef = useRef(null);
  const boardRef = useRef(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      const trs = gsap.utils.toArray(".spec-table tr");

      // 1. Initial State
      gsap.set(boardRef.current, { autoAlpha: 0, y: 80, scale: 0.96 });
      gsap.set(trs, { autoAlpha: 0, x: 50 });

      // 2. Scroll Pinned Timeline
      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: sectionRef.current,
          start: "top top",
          end: "+=120%", // slow cinematic scroll scrub
          pin: true,
          scrub: 1.2,
          pinSpacing: true,
        }
      });

      tl.to(boardRef.current, { autoAlpha: 1, y: 0, scale: 1, duration: 0.4 })
        // Stagger table rows one-by-one
        .to(trs, {
          autoAlpha: 1,
          x: 0,
          stagger: 0.1,
          duration: 0.5,
        }, 0.2)
        // Settle & pulse border glow
        .to(boardRef.current, {
          borderColor: "rgba(212, 168, 83, 0.32)",
          duration: 0.15,
        }, 0.85);

    }, sectionRef);

    return () => ctx.revert();
  }, []);

  return (
    <section ref={sectionRef} className="model-spec-section" data-section>
      <div className="spec-heading">
        <p className="section-label">Model card</p>
        <h2>Open enough to understand. Strict enough to trust.</h2>
      </div>

      <div ref={boardRef} className="spec-board">
        <div className="spec-board__intro">
          <span>ALTERSCORE-1</span>
          <p>
            A borrower-facing scoring interface designed around clarity: every answer becomes a governed
            input, every output comes with reasons, and every recourse path is written in plain language.
          </p>
        </div>

        <table className="spec-table">
          <tbody>
            {rows.map(([label, value]) => (
              <tr key={label}>
                <th>{label}</th>
                <td>{value}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
