export default function CounterfactualCards({ actions }) {
  return (
    <div className="result-panel">
      <div className="panel-heading">
        <p className="eyebrow">Counterfactuals</p>
        <h2>Moves that can lift you</h2>
      </div>
      <div className="counterfactual-grid">
        {actions.map((action) => (
          <article className="counter-card" key={`${action.feature}-${action.estimated_score_gain}`}>
            <strong>+{action.estimated_score_gain} pts</strong>
            <p>{action.plain_language}</p>
          </article>
        ))}
      </div>
    </div>
  );
}
