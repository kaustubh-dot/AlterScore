import React, { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Brain, ShieldAlert, Cpu, HeartHandshake, Eye } from 'lucide-react';
import SignalCanvas from '../components/hero/SignalCanvas';
import './Landing.css';

// Count-up helper hook
function useCountUp(target, duration = 1500, startCount = false) {
  const [count, setCount] = useState(0);

  useEffect(() => {
    if (!startCount) return;
    
    // Parse target to understand float vs integer
    const isFloat = target.toString().includes('.');
    const targetVal = parseFloat(target);
    if (isNaN(targetVal)) return;

    let start = 0;
    const startTime = performance.now();

    const updateCount = (timestamp) => {
      const elapsed = timestamp - startTime;
      const progress = Math.min(elapsed / duration, 1);
      
      // Easing curve (easeOutQuad)
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
        setCount(target); // Force final exact value
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

    // Setup intersection observer for stats counting
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

  // Set up stats count-ups
  const stat1 = useCountUp(1.4, 2000, triggerStats); // 1.4B
  const stat2 = useCountUp(39, 1500, triggerStats); // 39 features
  const stat3 = useCountUp(0.76, 2000, triggerStats); // 0.76 AUC
  const stat4 = useCountUp(5, 1200, triggerStats); // 5 min

  const startAssessment = () => {
    navigate('/assessment');
  };

  return (
    <div className="landing-page">
      {/* Hero Section */}
      <header className="landing-hero" id="hero">
        <SignalCanvas />
        <div className="hero-content container">
          <p className="hero-eyebrow animate-fade-up">Cognitive Credit System</p>
          <h1 className="hero-headline animate-fade-up">
            Credit intelligence <br />
            beyond <em>history</em>.
          </h1>
          <p className="hero-subhead animate-fade-up">
            We read how you think, how you decide, and how you recover — not what traditional banks have recorded about you.
          </p>
          <div className="hero-cta animate-fade-up">
            <button onClick={startAssessment} className="btn btn-primary btn-large">
              <span>Start Assessment</span>
              <ArrowRight size={16} />
            </button>
          </div>
          <div className="hero-meta animate-fade-up">
            <span>27 Questions</span>
            <span className="hero-meta-dot">•</span>
            <span>~5 Minutes</span>
            <span className="hero-meta-dot">•</span>
            <span>Instant Decisions</span>
          </div>
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
            <h2 className="section-title">What We Measure</h2>
            <p className="section-desc">
              AlterScore operates beyond transactional ledgers, looking directly at structural cognitive styles.
            </p>
          </div>

          <div className="features-grid">
            <div className="feature-card" style={{ '--card-accent': 'var(--accent-primary)' }}>
              <div className="feature-icon-wrapper">
                <Brain size={24} />
              </div>
              <h3 className="feature-title">Cognitive Reflection</h3>
              <p className="feature-text">
                Evaluates analytical reasoning, delay discounting, and numerical reasoning through logic traps. We measure the split-second balance between instinct and deliberation.
              </p>
            </div>

            <div className="feature-card" style={{ '--card-accent': 'var(--accent-cyan)' }}>
              <div className="feature-icon-wrapper">
                <Eye size={24} />
              </div>
              <h3 className="feature-title">Silent Telemetry</h3>
              <p className="feature-text">
                Our lightweight sensors observe hesitation patterns, mouse/scroll speed, answer changes, and temporal delays. We capture the friction of decision-making.
              </p>
            </div>

            <div className="feature-card" style={{ '--card-accent': 'var(--accent-emerald)' }}>
              <div className="feature-icon-wrapper">
                <HeartHandshake size={24} />
              </div>
              <h3 className="feature-title">Resilience & Agency</h3>
              <p className="feature-text">
                A localized, semantic NLP scanner analyzes open descriptions of financial crisis to identify problem-solving orientation, locus of control, and personal accountability.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="section section-how">
        <div className="container">
          <div className="section-header">
            <span className="section-eyebrow">System Stepper</span>
            <h2 className="section-title">How It Works</h2>
            <p className="section-desc">
              A clinical, friction-free journey from cognitive profiling to a credit tier verdict.
            </p>
          </div>

          <div className="stepper-row">
            <div className="step-node">
              <div className="step-number">01</div>
              <h3 className="step-title">Answer Questions</h3>
              <p className="step-desc">Respond to 27 cognitive puzzles and behavioral scenarios designed to profile your agency.</p>
            </div>
            
            <div className="step-arrow">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path className="arrow-path" d="M5 12h14M13 6l6 6-6 6" />
              </svg>
            </div>

            <div className="step-node">
              <div className="step-number">02</div>
              <h3 className="step-title">Extract Signals</h3>
              <p className="step-desc">Our backend extracts 39 features, including semantic indicators and telemetry speeds.</p>
            </div>

            <div className="step-arrow">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path className="arrow-path" d="M5 12h14M13 6l6 6-6 6" />
              </svg>
            </div>

            <div className="step-node">
              <div className="step-number">03</div>
              <h3 className="step-title">Get Score</h3>
              <p className="step-desc">Get an instant score between 300 and 850, complete with SHAP explanations and actionable counterfactuals.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="section section-stats" ref={statsRef}>
        <div className="container">
          <div className="stats-grid">
            <div className="stat-item">
              <div className="stat-number">{triggerStats ? `${stat1}B` : '0B'}</div>
              <div className="stat-label">Unbanked Adults Globally</div>
            </div>
            <div className="stat-item">
              <div className="stat-number">{triggerStats ? stat2 : '0'}</div>
              <div className="stat-label">Behavioral Features</div>
            </div>
            <div className="stat-item">
              <div className="stat-number">{triggerStats ? stat3 : '0.00'}</div>
              <div className="stat-label">Model AUC Score</div>
            </div>
            <div className="stat-item">
              <div className="stat-number">{triggerStats ? `${stat4} min` : '0 min'}</div>
              <div className="stat-label">Average Time to Score</div>
            </div>
          </div>
        </div>
      </section>

      {/* Final CTA Section */}
      <section className="final-cta">
        <SignalCanvas />
        <div className="cta-container container">
          <h2 className="cta-title">Ready to be seen differently?</h2>
          <p className="cta-sub">
            Begin your psychometric assessment. Your cognitive credentials are the only collateral required.
          </p>
          <button onClick={startAssessment} className="btn btn-primary">
            <span>Begin Assessment</span>
            <ArrowRight size={16} />
          </button>
        </div>
      </section>
    </div>
  );
}
