import React, { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
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

    let start = 0;
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
  const navigate = useNavigate();
  const [hideScroll, setHideScroll] = useState(false);
  const [triggerStats, setTriggerStats] = useState(false);
  const statsRef = useRef(null);

  useEffect(() => {
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

    return () => {
      window.removeEventListener('scroll', handleScroll);
      if (statsRef.current) observer.disconnect();
    };
  }, []);

  const stat1 = useCountUp(1.4, 2000, triggerStats);
  const stat2 = useCountUp(39, 1500, triggerStats);
  const stat3 = useCountUp(0.76, 2000, triggerStats);
  const stat4 = useCountUp(5, 1200, triggerStats);

  const startAssessment = () => {
    navigate('/assessment');
  };

  return (
    <div className="landing-page">
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
          <span>Scroll to probe</span>
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
              </GlowCard>
            </ScrollReveal>

            <ScrollReveal direction="scale" delay={200} className="feature-reveal">
              <GlowCard className="feature-card">
                <div className="feature-icon-wrapper">
                  <Eye size={20} />
                </div>
                <h3 className="feature-title">Silent Telemetry</h3>
              </GlowCard>
            </ScrollReveal>

            <ScrollReveal direction="scale" delay={300} className="feature-reveal">
              <GlowCard className="feature-card">
                <div className="feature-icon-wrapper">
                  <HeartHandshake size={20} />
                </div>
                <h3 className="feature-title">Resilience & Agency</h3>
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
                </GlowCard>
              </ScrollReveal>

              <ScrollReveal direction="up" delay={250} className="step-reveal">
                <GlowCard className="step-node">
                  <div className="step-number-wrapper">
                    <span className="step-number">02</span>
                  </div>
                  <h3 className="step-title">Parse Telemetry</h3>
                </GlowCard>
              </ScrollReveal>

              <ScrollReveal direction="up" delay={400} className="step-reveal">
                <GlowCard className="step-node">
                  <div className="step-number-wrapper">
                    <span className="step-number">03</span>
                  </div>
                  <h3 className="step-title">Score Verdict</h3>
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
    </div>
  );
}
