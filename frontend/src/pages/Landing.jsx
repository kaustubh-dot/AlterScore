import { useEffect, useState } from 'react';
import usePageTransition from '../hooks/usePageTransition';
import {
  ArrowRight,
  Brain,
  CheckCircle2,
  Eye,
  GitBranch,
  HeartHandshake,
  ShieldCheck,
} from 'lucide-react';
import SignalCanvas from '../components/hero/SignalCanvas';
import MagneticButton from '../components/ui/MagneticButton';
import Modal from '../components/ui/Modal';
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
  const [assessmentChooserOpen, setAssessmentChooserOpen] = useState(false);

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
    setAssessmentChooserOpen(true);
  };
  const chooseAssessment = (mode) => {
    setAssessmentChooserOpen(false);
    transitionTo(mode === 'trial' ? '/assessment?mode=trial' : '/assessment');
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

              <p className="hero-sub">
                For students, first-time earners, and anyone building confidence with
                money: work through practical decisions, then see what you understand,
                what needs attention, and why.
              </p>

              <div className="hero-cta">
                <MagneticButton onClick={startAssessment} className="btn-large" variant="primary">
                  <span>Start assessment</span>
                  <ArrowRight size={14} aria-hidden="true" />
                </MagneticButton>
                <a className="btn btn-ghost btn-large hero-preview-link" href="#sample-result">
                  Preview a sample result
                </a>
              </div>

              <div className="hero-meta">
                <span>Quick trial: 5 questions • Full: {questionCount} required items + optional reflection</span>
              </div>
            </div>

            <div className={`scroll-indicator ${hideScroll ? 'hidden' : ''}`}>
              <span>Scroll to explore</span>
              <div className="scroll-arrow">↓</div>
            </div>
          </header>

          <section className="section sample-section" id="sample-result" aria-labelledby="sample-result-title">
            <div className="container">
              <div className="section-header sample-section-header">
                <div>
                  <h2 className="section-title" id="sample-result-title">
                    See the outcome first
                  </h2>
                </div>
                <p>
                  This illustrative result shows the experience waiting after the full
                  assessment. Real results are calculated and signed by the server.
                </p>
              </div>

              <div className="sample-result-shell">
                  <div className="sample-score-panel">
                    <div className="sample-proof">
                      <ShieldCheck size={15} aria-hidden="true" />
                      <span>Illustrative preview</span>
                    </div>
                    <div className="sample-score-ring" role="img" aria-label="Sample Financial Decision Index 72 out of 100">
                      <span>Financial Decision Index</span>
                      <strong>72</strong>
                      <small>0–100</small>
                    </div>
                    <p>A learning snapshot of financial knowledge and decision readiness.</p>
                  </div>

                  <div className="sample-insight-panel">
                    <h3>A score that explains itself.</h3>
                    <div className="sample-domain-grid" aria-label="Sample domain scores">
                      <div>
                        <span>Financial knowledge</span>
                        <strong>78.00</strong>
                      </div>
                      <div>
                        <span>Decision judgement</span>
                        <strong>66.40</strong>
                      </div>
                    </div>
                    <div className="sample-insight-list">
                      <div>
                        <CheckCircle2 size={18} aria-hidden="true" />
                        <p><strong>Next focus</strong> Compare total borrowing cost before choosing a lower monthly payment.</p>
                      </div>
                      <div>
                        <GitBranch size={18} aria-hidden="true" />
                        <p><strong>Decision replay</strong> See how each choice changed cash, obligations, and the next scenario.</p>
                      </div>
                    </div>
                    <button type="button" className="btn btn-primary sample-start-button" onClick={startAssessment}>
                      Get my own result <ArrowRight size={15} aria-hidden="true" />
                    </button>
                  </div>
                </div>
            </div>
          </section>

          {/* What We Measure Section */}
          <section className="section section-features">
            <div className="container">
              <div className="section-header">
                <h2 className="section-title">What the assessment covers</h2>
              </div>

              <div className="features-grid">
                <article className="feature-card feature-card-primary">
                    <div className="feature-icon-wrapper">
                      <Brain size={20} aria-hidden="true" />
                    </div>
                    <h3 className="feature-title">Financial fundamentals</h3>
                    <p className="feature-desc">
                      Short calculations cover cash flow, borrowing costs, inflation,
                      due dates, repayment, and emergency buffers.
                    </p>
                </article>

                <article className="feature-card">
                    <div className="feature-icon-wrapper">
                      <Eye size={20} aria-hidden="true" />
                    </div>
                    <h3 className="feature-title">Real-world decisions</h3>
                    <p className="feature-desc">
                      Choose between plausible options in practical money situations.
                      Each decision changes what happens next.
                    </p>
                </article>

                <article className="feature-card">
                    <div className="feature-icon-wrapper">
                      <HeartHandshake size={20} aria-hidden="true" />
                    </div>
                    <h3 className="feature-title">Planning habits</h3>
                    <p className="feature-desc">
                      Optional questions help you reflect on everyday habits. They are
                      shown separately and never change your score.
                    </p>
                </article>
              </div>
            </div>
          </section>

          {/* How It Works Section */}
          <section className="section section-how">
            <div className="container">
              <div className="section-header">
                <h2 className="section-title">How it works</h2>
              </div>

              <div className="stepper-row-container">
                <div className="stepper-row">
                  <article className="step-node">
                      <div className="step-number-wrapper">
                        <span className="step-number">01</span>
                      </div>
                      <h3 className="step-title">Answer the assessment</h3>
                      <p className="step-desc">
                        Complete {questionCount} required calculations and scenarios,
                        then add an optional reflection. No documents, identity, or
                        credit history are needed.
                      </p>
                  </article>

                  <article className="step-node">
                      <div className="step-number-wrapper">
                        <span className="step-number">02</span>
                      </div>
                      <h3 className="step-title">Apply the readiness rubric</h3>
                      <p className="step-desc">
                        Your answers are scored against one consistent rubric. Device
                        tracking and browsing data are never part of the result.
                      </p>
                  </article>

                  <article className="step-node">
                      <div className="step-number-wrapper">
                        <span className="step-number">03</span>
                      </div>
                      <h3 className="step-title">View the signed summary</h3>
                      <p className="step-desc">
                        Get the readiness index, domain summaries, limitations, and
                        a verification link and evidence you can inspect.
                      </p>
                  </article>
                </div>
              </div>
            </div>
          </section>

          {/* Final CTA Section */}
          <section className="final-cta">
            <SignalCanvas />
            <div className="cta-container container">
              <h2 className="cta-title">Turn decisions into direction.</h2>
              <p className="cta-subtitle">Five minutes. No account, documents, or credit history.</p>
              <div className="cta-btn-wrapper">
                <MagneticButton onClick={startAssessment} variant="primary">
                  <span>Start assessment</span>
                  <ArrowRight size={14} aria-hidden="true" />
                </MagneticButton>
              </div>
            </div>
          </section>
          <Modal
            isOpen={assessmentChooserOpen}
            title="Choose your assessment"
            message="Preview the experience in about two minutes, or complete the full assessment for calibrated, server-signed analysis."
            onCancel={() => setAssessmentChooserOpen(false)}
            actionsClassName="assessment-chooser-actions"
            actions={(
              <>
                <button type="button" className="btn btn-ghost" onClick={() => setAssessmentChooserOpen(false)}>Cancel</button>
                <button type="button" className="btn btn-secondary" onClick={() => chooseAssessment('trial')}>Quick trial · 5 questions</button>
                <button type="button" className="btn btn-primary" onClick={() => chooseAssessment('full')}>Full assessment</button>
              </>
            )}
          />
        </>
      )}
    </main>
  );
}
