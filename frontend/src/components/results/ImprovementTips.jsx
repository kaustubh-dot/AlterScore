export default function ImprovementTips({ tips }) {
  return (
    <section className="result-panel result-animate">
      <div className="panel-heading">
        <p className="eyebrow">Improvement tips</p>
        <h2>Next best actions</h2>
      </div>
      <div className="tips-list">
        {tips.map((tip) => (
          <article key={`${tip.feature}-${tip.title}`}>
            <strong>{tip.title}</strong>
            <p>{tip.body}</p>
          </article>
        ))}
      </div>
    </section>
  );
}
