export default function ShapBars({ explanation }) {
  const maxFactor = Math.max(...explanation.map((factor) => Math.abs(factor.shap_value)), 0.01);

  return (
    <section className="result-panel result-animate">
      <div className="panel-heading">
        <p className="eyebrow">SHAP explanation</p>
        <h2>What shaped the score</h2>
      </div>
      <div className="shap-list">
        {explanation.map((factor) => {
          const positive = factor.direction === "positive";
          const width = Math.max((Math.abs(factor.shap_value) / maxFactor) * 100, 3);
          return (
            <article className="shap-row" key={`${factor.feature}-${factor.shap_value}`} data-cursor="interactive">
              <div>
                <strong>{factor.display_name}</strong>
                <p>{factor.plain_language}</p>
              </div>
              <div className="shap-track">
                <span
                  className={`shap-fill ${positive ? "is-positive" : "is-negative"}`}
                  style={{ width: `${width}%` }}
                />
                <em>{factor.plain_language}</em>
              </div>
              <span className={positive ? "factor-badge is-positive" : "factor-badge is-negative"}>
                {positive ? "+" : "-"} {Math.abs(factor.shap_value).toFixed(2)}
              </span>
            </article>
          );
        })}
      </div>
    </section>
  );
}
