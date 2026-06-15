import { useEffect, useState, useRef } from 'react';
import usePageTransition from '../hooks/usePageTransition';
import { ArrowRight, Brain, HeartHandshake, Eye } from 'lucide-react';
import SignalCanvas from '../components/hero/SignalCanvas';
import ScrollReveal from '../components/animation/ScrollReveal';
import GlowCard from '../components/ui/GlowCard';
import MagneticButton from '../components/ui/MagneticButton';
import TextReveal from '../components/animation/TextReveal';
import './Landing.css';

// Count-up helper hook
function useCountUp(target, duration = 1500, startCount = false) {
  const [count, setCount] = useState(0);

  useEffect(() => {
    if (!startCount) return;
    
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
  const [isLoaded, setIsLoaded] = useState(() => document.body.classList.contains('preloader-done'));
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

  const stat1 = useCountUp(1.4, 2000, triggerStats);
  const stat2 = useCountUp(39, 1500, triggerStats);
  const stat3 = useCountUp(0.76, 2000, triggerStats);
  const stat4 = useCountUp(5, 1200, triggerStats);

  const startAssessment = () => {
    transitionTo('/assessment');
  };

  return (
    <div className={`landing-page ${isLoaded ? 'loaded' : ''}`} style={!isLoaded ? { opacity: 0, pointerEvents: 'none' } : undefined}>
      {isLoaded && (
        <>
          {/* Hero Section */}
          <header className="landing-hero" id="hero">
            <SignalCanvas />
            <div className="hero-content container">
              <div style={{ marginBottom: '16px' }}>
                <TextReveal text="Cognitive Credit System" delay={100} />
              </div>
              
              <h1 className="hero-headline">
                <TextReveal text="Credit intelligence" delay={250} /> <br />
                <TextReveal text="beyond history." delay={450} />
              </h1>

              <ScrollReveal direction="up" delay={550}>
                <p className="hero-sub">
                  AlterScore reads how you reason, decide, and write — not what
                  you've borrowed — to fairly score the 1.4&nbsp;billion adults the
                  credit bureau never sees. A five-minute assessment returns an
                  explainable 300–850 score and the reasons behind it.
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
                  <span>27 Questions • ~5 Minutes • Instant Decision</span>
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
                <span className="section-eyebrow">Interactive Sensors</span>
                <h2 className="section-title"><TextReveal text="What We Measure" /></h2>
              </div>

              <div className="features-grid">
                <ScrollReveal direction="scale" delay={100} className="feature-reveal">
                  <GlowCard className="feature-card">
                    <div className="feature-icon-wrapper">
                      <Brain size={20} />
                    </div>
                    <h3 className="feature-title">Cognitive Reflection</h3>
                    <p className="feature-desc">
                      Numeracy and reasoning tasks reveal how you weigh risk and
                      resist fast, intuitive errors under uncertainty.
                    </p>
                  </GlowCard>
                </ScrollReveal>

                <ScrollReveal direction="scale" delay={200} className="feature-reveal">
                  <GlowCard className="feature-card">
                    <div className="feature-icon-wrapper">
                      <Eye size={20} />
                    </div>
                    <h3 className="feature-title">Silent Telemetry</h3>
                    <p className="feature-desc">
                      Response timing, hesitation, and revisions are captured
                      passively — signals of deliberation no form can ask for.
                    </p>
                  </GlowCard>
                </ScrollReveal>

                <ScrollReveal direction="scale" delay={300} className="feature-reveal">
                  <GlowCard className="feature-card">
                    <div className="feature-icon-wrapper">
                      <HeartHandshake size={20} />
                    </div>
                    <h3 className="feature-title">Resilience & Agency</h3>
                    <p className="feature-desc">
                      Scenario choices and open text surface future orientation,
                      conscientiousness, and how you plan when resources are tight.
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
                      <h3 className="step-title">Profile Agency</h3>
                      <p className="step-desc">
                        Answer 27 adaptive questions in about five minutes — no
                        documents or credit history required.
                      </p>
                    </GlowCard>
                  </ScrollReveal>

                  <ScrollReveal direction="up" delay={250} className="step-reveal">
                    <GlowCard className="step-node">
                      <div className="step-number-wrapper">
                        <span className="step-number">02</span>
                      </div>
                      <h3 className="step-title">Parse Telemetry</h3>
                      <p className="step-desc">
                        Behavioral signals and language are scored by a calibrated,
                        governance-gated machine learning model.
                      </p>
                    </GlowCard>
                  </ScrollReveal>

                  <ScrollReveal direction="up" delay={400} className="step-reveal">
                    <GlowCard className="step-node">
                      <div className="step-number-wrapper">
                        <span className="step-number">03</span>
                      </div>
                      <h3 className="step-title">Score Verdict</h3>
                      <p className="step-desc">
                        Get a 300–850 score with its risk band, SHAP explanations,
                        and concrete actions to improve over time.
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
                    <div className="stat-number">{triggerStats ? `${stat1}B` : '0B'}</div>
                    <div className="stat-label">Unbanked Adults</div>
                  </div>
                </ScrollReveal>
                
                <ScrollReveal direction="up" delay={200}>
                  <div className="stat-item">
                    <div className="stat-number">{triggerStats ? stat2 : '0'}</div>
                    <div className="stat-label">Behavioral Features</div>
                  </div>
                </ScrollReveal>

                <ScrollReveal direction="up" delay={300}>
                  <div className="stat-item">
                    <div className="stat-number">{triggerStats ? stat3 : '0.00'}</div>
                    <div className="stat-label">Model AUC</div>
                  </div>
                </ScrollReveal>

                <ScrollReveal direction="up" delay={400}>
                  <div className="stat-item">
                    <div className="stat-number">{triggerStats ? `${stat4}m` : '0m'}</div>
                    <div className="stat-label">Time to Score</div>
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
                  <TextReveal text="Ready to be seen differently?" />
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
