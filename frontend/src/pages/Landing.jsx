import { useEffect, useState } from 'react';
import usePageTransition from '../hooks/usePageTransition';
import { ArrowRight, Brain, HeartHandshake, Eye } from 'lucide-react';
import SignalCanvas from '../components/hero/SignalCanvas';
import ScrollReveal from '../components/animation/ScrollReveal';
import GlowCard from '../components/ui/GlowCard';
import MagneticButton from '../components/ui/MagneticButton';
import TextReveal from '../components/animation/TextReveal';
import { PUBLIC_ASSESSMENT_ITEM_COUNT } from '../lib/assessmentV2';
import { getSessionStorage, readStorageItem } from '../lib/safeStorage';
import './Landing.css';

function hasCompletedPreload() {
  return (
    document.body.classList.contains('preloader-done')
    || readStorageItem(getSessionStorage(), 'alterscore_preloader_seen') === 'true'
  );
}

export default function Landing() {
  const { transitionTo } = usePageTransition();
  const [isLoaded, setIsLoaded] = useState(hasCompletedPreload);
  const [hideScroll, setHideScroll] = useState(false);

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

    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, [isLoaded]);

  const startAssessment = () => {
    transitionTo('/assessment');
  };
  const questionCount = PUBLIC_ASSESSMENT_ITEM_COUNT;

  return (
    <main className={`landing-page ${isLoaded ? 'loaded' : ''}`} style={!isLoaded ? { opacity: 0, pointerEvents: 'none' } : undefined}>
      {isLoaded && (
        <>
          {/* Hero Section */}
          <header className="landing-hero" id="hero">
            <SignalCanvas />
            <div className="hero-content container">
              <h1 className="hero-headline">
                <TextReveal text="Financial readiness," delay={250} /> <br />
                <TextReveal text="made clear." delay={450} />
              </h1>

              <ScrollReveal direction="up" delay={550}>
                <p className="hero-sub">
                  Work through practical money decisions and get a clear 0–100 readiness
                  score, with a familiar 300–850 view. It is an educational snapshot, not
                  a credit score or lending decision.
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
                  <span>{questionCount} required items • optional reflection • ~5 minutes</span>
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
                    <h3 className="feature-title">Financial fundamentals</h3>
                    <p className="feature-desc">
                      Short calculations cover cash flow, borrowing costs, inflation,
                      due dates, repayment, and emergency buffers.
                    </p>
                  </GlowCard>
                </ScrollReveal>

                <ScrollReveal direction="scale" delay={200} className="feature-reveal">
                  <GlowCard className="feature-card">
                    <div className="feature-icon-wrapper">
                      <Eye size={20} />
                    </div>
                    <h3 className="feature-title">Real-world decisions</h3>
                    <p className="feature-desc">
                      Choose between plausible options in practical money situations.
                      Each decision changes what happens next.
                    </p>
                  </GlowCard>
                </ScrollReveal>

                <ScrollReveal direction="scale" delay={300} className="feature-reveal">
                  <GlowCard className="feature-card">
                    <div className="feature-icon-wrapper">
                      <HeartHandshake size={20} />
                    </div>
                    <h3 className="feature-title">Planning habits</h3>
                    <p className="feature-desc">
                      Optional questions help you reflect on everyday habits. They are
                      shown separately and never change your score.
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
                <span className="section-eyebrow">Three simple steps</span>
                <h2 className="section-title"><TextReveal text="How it works" /></h2>
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
                        Complete {questionCount} required calculations and scenarios,
                        then add an optional reflection. No documents, identity, or
                        credit history are needed.
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
                        Your answers are scored against one consistent rubric. Device
                        tracking and browsing data are never part of the result.
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

          {/* Final CTA Section */}
          <section className="final-cta">
            <SignalCanvas />
            <div className="cta-container container">
              <ScrollReveal direction="scale">
                <h2 className="cta-title">
                  <TextReveal text="See where you stand." />
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
    </main>
  );
}
