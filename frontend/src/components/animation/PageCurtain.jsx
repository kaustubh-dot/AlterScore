import './PageCurtain.css';

export default function PageCurtain({ state }) {
  if (state === 'idle') return null;

  return (
    <div className={`page-curtain ${state}`}>
      <div className="curtain-panel top-panel" />
      <div className="curtain-brand">
        <span className="curtain-brand-text">AlterScore</span>
      </div>
      <div className="curtain-panel bottom-panel" />
    </div>
  );
}
