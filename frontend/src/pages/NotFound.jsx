import { ArrowLeft, ClipboardList, MapPinOff } from 'lucide-react';
import usePageTransition from '../hooks/usePageTransition';
import './NotFound.css';

export default function NotFound() {
  const { transitionTo } = usePageTransition();

  return (
    <main className="not-found-page" aria-labelledby="not-found-title">
      <div className="not-found-shell container">
        <div className="not-found-code font-mono" aria-hidden="true">404</div>
        <div className="not-found-kicker font-mono">
          <MapPinOff size={15} aria-hidden="true" />
          <span>ROUTE UNAVAILABLE</span>
        </div>
        <h1 id="not-found-title">This page is outside the assessment.</h1>
        <p>
          The address does not match an AlterScore page. Your browser-session
          result, if one exists, has not been changed.
        </p>
        <div className="not-found-actions">
          <button type="button" className="btn btn-secondary" onClick={() => transitionTo('/')}>
            <ArrowLeft size={16} aria-hidden="true" />
            Return home
          </button>
          <button type="button" className="btn btn-primary" onClick={() => transitionTo('/assessment')}>
            <ClipboardList size={16} aria-hidden="true" />
            Start assessment
          </button>
        </div>
      </div>
    </main>
  );
}
