import { ArrowLeft, FlaskConical, LockKeyhole } from 'lucide-react';
import usePageTransition from '../hooks/usePageTransition';
import './ResearchLab.css';

export default function ResearchLab() {
  const { transitionTo } = usePageTransition();

  return (
    <main className="research-lab-page">
      <div className="research-lab-shell container">
        <header className="research-lab-hero">
          <div className="research-lab-kicker font-mono">
            <FlaskConical size={15} aria-hidden="true" />
            <span>OFFLINE SYNTHETIC RESEARCH</span>
          </div>
          <h1>Research Lab</h1>
          <p className="research-lab-lede">
            A static guide to the archived model experiments that informed the
            project. Nothing on this page calls a research route or scores a
            public assessment.
          </p>
        </header>

        <section className="research-lab-grid" aria-label="Research boundaries">
          <article className="research-lab-card">
            <span className="research-lab-label font-mono">DATA ORIGIN</span>
            <h2>Synthetic labels and fairness reports</h2>
            <p>
              The archived labels, evaluation reports, and fairness summaries
              were generated for research demonstrations. They are not
              measurements of real borrowers, repayment outcomes, or population
              fairness.
            </p>
          </article>

          <article className="research-lab-card">
            <span className="research-lab-label font-mono">METRIC MEANING</span>
            <h2>AUC measures generated-data recovery</h2>
            <p>
              Any AUC or calibration value describes how well an archived model
              recovered its synthetic training signal on generated data. It is not external
              validation, repayment prediction, creditworthiness, or lending
              evidence.
            </p>
          </article>

          <article className="research-lab-card research-lab-card-wide">
            <span className="research-lab-label font-mono">PUBLIC BOUNDARY</span>
            <h2>The model does not score public assessments</h2>
            <p>
              Public assessments use the anonymous, deterministic v2 Financial
              Decision Readiness contract. The archived synthetic model,
              explainers, parsers, analytics, and training dependencies are
              separated from that serving path.
            </p>
            <div className="research-lab-lockline">
              <LockKeyhole size={16} aria-hidden="true" />
              <span>Research files are offline reference material only.</span>
            </div>
          </article>
        </section>

        <div className="research-lab-actions">
          <button
            type="button"
            className="btn btn-ghost"
            onClick={() => transitionTo('/')}
          >
            <ArrowLeft size={15} aria-hidden="true" />
            Return to demo
          </button>
        </div>
      </div>
    </main>
  );
}
