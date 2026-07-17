import { useEffect, useState, useRef } from 'react';
import usePageTransition from '../hooks/usePageTransition';
import { ArrowRight, Brain, HeartHandshake, Eye } from 'lucide-react';
import SignalCanvas from '../components/hero/SignalCanvas';
import ScrollReveal from '../components/animation/ScrollReveal';
import GlowCard from '../components/ui/GlowCard';
import MagneticButton from '../components/ui/MagneticButton';
import TextReveal from '../components/animation/TextReveal';
import { PUBLIC_ASSESSMENT_ITEM_COUNT } from '../lib/assessmentV2';
import { prefersReducedMotion } from '../lib/motionPreferences';
import { getSessionStorage, readStorageItem } from '../lib/safeStorage';
import './Landing.css';

function hasCompletedPreload() {
  return (
    document.body.classList.contains('preloader-done')
    || readStorageItem(getSessionStorage(), 'alterscore_preloader_seen') === 'true'
  );
}

// Count-up helper hook
function useCountUp(target, duration = 1500, startCount = false) {
  const [count, setCount] = useState(0);

  useEffect(() => {
    if (!startCount) return;
    if (prefersReducedMotion()) {
      const frame = requestAnimationFrame(() => setCount(target));
      return () => cancelAnimationFrame(frame);
    }
    
    const isFloat = target.toString().includes('.');
    const targetVal = parseFloat(target);
    if (isNaN(targetVal)) return;

    const startTime = performance.now();

    const updateCount = (timestamp) => {
      const elapsed = timestamp - startTime;
      const progress = Math.min(elapsed / duration, 1);
      
      const easeProgress = progress * (2 - progress);
      const current = easeProgress * targetVal;

      if (isFloat) {
        setCount(current.toFixed(2));
      } else {
        setCount(Math.floor(current));
      }

      if (progress < 1) {
        requestAnimationFrame(updateCount);
      } else {
        setCount(target);
      }
    };

    requestAnimationFrame(updateCount);
  }, [target, duration, startCount]);

  return count;
}

export default function Landing() {
  const { transitionTo } = usePageTransition();
  const [isLoaded, setIsLoaded] = useState(hasCompletedPreload);
  const [hideScroll, setHideScroll] = useState(false);
  const [triggerStats, setTriggerStats] = useState(false);
  const statsRef = useRef(null);

  useEffect(() => {
    if (isLoaded) return;
    const handlePreloadComplete = () => {
      setIsLoaded(true);
    };
    window.addEventListener('preloadComplete', handlePreloadComplete);
    return () => {
      window.removeEventListener('preloadComplete', handlePreloadComplete);
    };
  }, [isLoaded]);

  useEffect(() => {
    if (!isLoaded) return;

    const handleScroll = () => {
      if (window.scrollY > 80) {
        setHideScroll(true);
      } else {
        setHideScroll(false);
      }
    };

    window.addEventListener('scroll', handleScroll);

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setTriggerStats(true);
          observer.unobserve(entry.target);
        }
      },
      { threshold: 0.2 }
    );

    if (statsRef.current) {
      observer.observe(statsRef.current);
    }

    const currentStatsRef = statsRef.current;

    return () => {
      window.removeEventListener('scroll', handleScroll);
      if (currentStatsRef) observer.disconnect();
    };
  }, [isLoaded]);

  const stat1 = useCountUp(PUBLIC_ASSESSMENT_ITEM_COUNT, 1200, triggerStats);
  const stat2 = useCountUp(18, 1200, triggerStats);
  const stat3 = useCountUp(6, 1200, triggerStats);
  const stat4 = useCountUp(0, 1200, triggerStats);

  const startAssessment = () => {
    transitionTo('/assessment');
  };
  const questionCount = PUBLIC_ASSESSMENT_ITEM_COUNT;

  return (
    <div className={`landing-page ${isLoaded ? 'loaded' : ''}`} style={!isLoaded ? { opacity: 0, pointerEvents: 'none' } : undefined}>
      {isLoaded && (
        <>
          {/* Hero Section */}
          <header className="landing-hero" id="hero">
            <SignalCanvas />
            <div className="hero-content container">
              <div style={{ marginBottom: '16px' }}>
                <TextReveal text="Synthetic Assessment Demo" delay={100} />
              </div>
              
              <h1 className="hero-headline">
                <TextReveal text="Transparent scoring" delay={250} /> <br />
                <TextReveal text="for product testing." delay={450} />
              </h1>

              <ScrollReveal direction="up" delay={550}>
                <p className="hero-sub">
                  AlterScore is a synthetic educational demonstration of a server-issued
                  readiness assessment. It returns a 0–100 index and an illustrative
                  300–850 transformation — never a repayment prediction, lending decision,
                  eligibility result, or bureau score.
                </p>
              </ScrollReveal>

              <ScrollReveal direction="up" delay={650}>
                <div className="hero-cta">
                  <MagneticButton onClick={startAssessment} className="btn-large" variant="primary">
                    <span>Start Assessment</span>
                    <ArrowRight size={14} />
                  </MagneticButton>
                </div>
              </ScrollReveal>

              <ScrollReveal direction="up" delay={800}>
                <div className="hero-meta">
                  <span>{questionCount} Questions • ~5 Minutes • Illustrative Result</span>
                </div>
              </ScrollReveal>
            </div>

            <div className={`scroll-indicator ${hideScroll ? 'hidden' : ''}`}>
              <span>Scroll to explore</span>
              <div className="scroll-arrow">↓</div>
            </div>
          </header>

          {/* What We Measure Section */}
          <section className="section section-features">
            <div className="container">
              <div className="section-header">
                <span className="section-eyebrow">Assessment evidence</span>
                <h2 className="section-title"><TextReveal text="What the assessment covers" /></h2>
              </div>

              <div className="features-grid">
                <ScrollReveal direction="scale" delay={100} className="feature-reveal">
                  <GlowCard className="feature-card">
                    <div className="feature-icon-wrapper">
                      <Brain size={20} />
                    </div>
                    <h3 className="feature-title">Cognitive Reflection</h3>
                    <p className="feature-desc">
                      Objective items test financial knowledge with server-issued
                      values. The browser receives no answer keys or scoring rules.
                    </p>
                  </GlowCard>
                </ScrollReveal>

                <ScrollReveal direction="scale" delay={200} className="feature-reveal">
                  <GlowCard className="feature-card">
                    <div className="feature-icon-wrapper">
                      <Eye size={20} />
                    </div>
                    <h3 className="feature-title">Structured Scenarios</h3>
                    <p className="feature-desc">
                      Decision simulations present opaque, randomized options and
                      evaluate the selected path on the server. Timing and device data are not used.
                    </p>
                  </GlowCard>
                </ScrollReveal>

                <ScrollReveal direction="scale" delay={300} className="feature-reveal">
                  <GlowCard className="feature-card">
                    <div className="feature-icon-wrapper">
                      <HeartHandshake size={20} />
                    </div>
                    <h3 className="feature-title">Resilience & Planning</h3>
                    <p className="feature-desc">
                      Behavior reflection includes a Not applicable choice, is shown
                      separately from evidence, and never changes the index.
                    </p>
                  </GlowCard>
                </ScrollReveal>
              </div>
            </div>
          </section>

          {/* How It Works Section */}
          <section className="section section-how">
            <div className="container">
              <div className="section-header">
                <span className="section-eyebrow">System Stepper</span>
                <h2 className="section-title"><TextReveal text="How It Works" /></h2>
              </div>

              <div className="stepper-row-container">
                <div className="timeline-svg-wrapper">
                  <svg className="timeline-svg" width="100%" height="2" viewBox="0 0 100 2" preserveAspectRatio="none">
                    <line x1="0" y1="1" x2="100" y2="1" className="timeline-line-bg" />
                    <line x1="0" y1="1" x2="100" y2="1" className="timeline-line-active" />
                  </svg>
                </div>
                
                <div className="stepper-row">
                  <ScrollReveal direction="up" delay={100} className="step-reveal">
                    <GlowCard className="step-node">
                      <div className="step-number-wrapper">
                        <span className="step-number">01</span>
                      </div>
                      <h3 className="step-title">Answer the assessment</h3>
                      <p className="step-desc">
                        Answer {questionCount} server-issued items in about five minutes.
                        No documents, identity, or credit history are used.
                      </p>
                    </GlowCard>
                  </ScrollReveal>

                  <ScrollReveal direction="up" delay={250} className="step-reveal">
                    <GlowCard className="step-node">
                      <div className="step-number-wrapper">
                        <span className="step-number">02</span>
                      </div>
                      <h3 className="step-title">Apply the readiness rubric</h3>
                      <p className="step-desc">
                        The backend applies the frozen deterministic rubric. Browser
                        telemetry, device data, and hidden text signals are excluded.
                      </p>
                    </GlowCard>
                  </ScrollReveal>

                  <ScrollReveal direction="up" delay={400} className="step-reveal">
                    <GlowCard className="step-node">
                      <div className="step-number-wrapper">
                        <span className="step-number">03</span>
                      </div>
                      <h3 className="step-title">View the signed summary</h3>
                      <p className="step-desc">
                        Get the readiness index, domain summaries, limitations, and
                        a verification link — not a financial verdict.
                      </p>
                    </GlowCard>
                  </ScrollReveal>
                </div>
              </div>
            </div>
          </section>

          {/* Stats Section */}
          <section className="section section-stats" ref={statsRef}>
            <div className="container">
              <div className="stats-grid">
                <ScrollReveal direction="up" delay={100}>
                  <div className="stat-item">
                    <div className="stat-number">{triggerStats ? stat1 : '0'}</div>
                    <div className="stat-label">Assessment items</div>
                  </div>
                </ScrollReveal>
                
                <ScrollReveal direction="up" delay={200}>
                  <div className="stat-item">
                    <div className="stat-number">{triggerStats ? stat2 : '0'}</div>
                    <div className="stat-label">Scored items</div>
                  </div>
                </ScrollReveal>

                <ScrollReveal direction="up" delay={300}>
                  <div className="stat-item">
                    <div className="stat-number">{triggerStats ? stat3 : '0'}</div>
                    <div className="stat-label">Unscored reflections</div>
                  </div>
                </ScrollReveal>

                <ScrollReveal direction="up" delay={400}>
                  <div className="stat-item">
                    <div className="stat-number">{triggerStats ? stat4 : '0'}</div>
                    <div className="stat-label">Browser/device inputs</div>
                  </div>
                </ScrollReveal>
              </div>
            </div>
          </section>

          {/* Final CTA Section */}
          <section className="final-cta">
            <SignalCanvas />
            <div className="cta-container container">
              <ScrollReveal direction="scale">
                <h2 className="cta-title">
                  <TextReveal text="Ready to test the assessment?" />
                </h2>
              </ScrollReveal>
              <ScrollReveal direction="up" delay={200}>
                <div className="cta-btn-wrapper">
                  <MagneticButton onClick={startAssessment} variant="primary">
                    <span>Begin Assessment</span>
                    <ArrowRight size={14} />
                  </MagneticButton>
                </div>
              </ScrollReveal>
            </div>
          </section>
        </>
      )}
    </div>
  );
}
