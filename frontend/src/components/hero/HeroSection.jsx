import { useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

export default function HeroSection() {
  const containerRef = useRef(null);
  const logoRef = useRef(null);
  const cardRef = useRef(null);
  const copyRef = useRef(null);
  const actionsRef = useRef(null);
  const toplineRef = useRef(null);
  const scrollIndicatorRef = useRef(null);

  useEffect(() => {
    const ctx = gsap.context(() => {
      // 1. Page Load Entrance Choreography (Zero scroll)
      const entrance = gsap.timeline({ defaults: { ease: "power4.out" } });

      // Split words of logo for blur stagger rise
      const logoSpans = logoRef.current.querySelectorAll(".logo-word");
      
      gsap.set(logoSpans, { y: 120, autoAlpha: 0, filter: "blur(14px)" });
      gsap.set(toplineRef.current, { autoAlpha: 0, y: -20 });
      
      // Set initial hidden 3D-tilt states for scroll-revealed elements (Oryzo style)
      gsap.set(copyRef.current, { 
        autoAlpha: 0, 
        y: 80, 
        transformPerspective: 1200, 
        rotateX: 24 
      });
      gsap.set(actionsRef.current, { 
        autoAlpha: 0, 
        y: 80, 
        transformPerspective: 1200, 
        rotateX: 24 
      });
      gsap.set(cardRef.current, { 
        autoAlpha: 0, 
        y: 100, 
        scale: 0.94,
        transformPerspective: 1200, 
        rotateX: 22, 
        rotateY: 8 
      });
      gsap.set(scrollIndicatorRef.current, { autoAlpha: 0 });

      entrance
        .to(logoSpans, {
          y: 0,
          autoAlpha: 1,
          filter: "blur(0px)",
          duration: 1.4,
          stagger: 0.16,
        }, 0.1)
        .to(toplineRef.current, {
          autoAlpha: 1,
          y: 0,
          duration: 1.0,
        }, 0.5)
        .to(scrollIndicatorRef.current, {
          autoAlpha: 1,
          duration: 0.8,
        }, 1.2);

      // 2. Pinned Scroll-Triggered Timeline (Oryzo rotating/gradual reveals)
      const tl = gsap.timeline({
        scrollTrigger: {
          trigger: containerRef.current,
          start: "top top",
          end: "+=120%", // Clean pacing for gradual scroll reveal
          scrub: 1.2,
          pin: true,
          pinSpacing: true,
        }
      });

      // First part: Gradually show & rotate text/cards as user scrolls down
      tl.to(logoRef.current, {
        scale: 0.88,
        yPercent: -20,
        ease: "power1.out",
      }, 0)
      .to(copyRef.current, {
        autoAlpha: 1,
        y: 0,
        rotateX: 0,
        ease: "power2.out",
      }, 0.05)
      .to(cardRef.current, {
        autoAlpha: 1,
        y: 0,
        scale: 1,
        rotateX: 0,
        rotateY: 0,
        ease: "power2.out",
      }, 0.08)
      .to(actionsRef.current, {
        autoAlpha: 1,
        y: 0,
        rotateX: 0,
        ease: "power2.out",
      }, 0.16)
      .to(scrollIndicatorRef.current, {
        autoAlpha: 0,
        y: 40,
        ease: "none",
      }, 0);

      // Second part: Transition them away cleanly into background
      tl.to(logoRef.current, {
        opacity: 0.12,
        yPercent: -45,
        scale: 0.82,
        ease: "power1.in",
      }, 0.6)
      .to([copyRef.current, actionsRef.current, toplineRef.current], {
        opacity: 0.1,
        yPercent: -25,
        ease: "power1.in",
      }, 0.6)
      .to(cardRef.current, {
        opacity: 0.15,
        yPercent: -60,
        scale: 1.06,
        rotate: -3,
        ease: "power1.in",
      }, 0.6);

    }, containerRef);

    return () => ctx.revert();
  }, []);

  return (
    <section ref={containerRef} className="hero-section" data-section>
      <div ref={toplineRef} className="hero-topline">
        <span>Built for borrowers beyond the bureau.</span>
        <span>AlterScore v0.2.0</span>
      </div>

      <div ref={logoRef} className="hero-logo-container">
        <div className="hero-logo" aria-label="AlterScore">
          <span className="logo-word">ALTER</span>
          <span className="logo-word stroke-text">SCORE</span>
        </div>
      </div>

      <div className="hero-mid-split">
        <div className="hero-copy">
          <p ref={copyRef}>
            A quiet assessment that turns financial judgement, behavior, and resilience into an explainable score.
          </p>
          <div ref={actionsRef} className="hero-actions">
            <Link className="pill-button pill-button--primary" to="/assessment" data-magnetic>
              Begin assessment
            </Link>
            <a className="pill-button" href="#manifesto" data-magnetic>
              Scroll the model
            </a>
          </div>
        </div>

        {/* Floating Glassmorphic Telemetry Card */}
        <div ref={cardRef} className="hero-glass-card" data-cursor="interactive">
          <div className="card-glare" />
          <div className="card-header">
            <span className="mono-text">// ENGINE STATUS: ACTIVE</span>
            <span className="status-dot pulsing" />
          </div>
          <div className="card-body">
            <div className="model-label">ALTERSCORE-1</div>
            <div className="model-sub">MONOTONIC BOOSTER ENSEMBLE</div>
            
            <div className="telemetry-rows">
              <div className="tele-row">
                <span>Fairness proxy checks</span>
                <span className="tele-val text-gold">PASS</span>
              </div>
              <div className="tele-row">
                <span>Recourse mapping</span>
                <span className="tele-val text-gold">READY</span>
              </div>
              <div className="tele-row">
                <span>Attributions</span>
                <span className="tele-val">SHAP 99.4%</span>
              </div>
            </div>

            <div className="card-mini-chart">
              <svg viewBox="0 0 200 40" width="100%" height="40" fill="none">
                <path d="M0,35 Q30,25 60,30 T120,10 T180,18 T200,5" stroke="var(--accent-gold)" strokeWidth="2" strokeLinecap="round" />
                <path d="M0,35 Q30,25 60,30 T120,10 T180,18 T200,5 L200,40 L0,40 Z" fill="url(#chart-grad)" opacity="0.15" />
                <defs>
                  <linearGradient id="chart-grad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="var(--accent-gold)" />
                    <stop offset="100%" stopColor="transparent" />
                  </linearGradient>
                </defs>
              </svg>
            </div>
          </div>
        </div>
      </div>

      <div ref={scrollIndicatorRef} className="scroll-indicator">
        <span>Scroll to continue</span>
        <i />
      </div>
    </section>
  );
}
