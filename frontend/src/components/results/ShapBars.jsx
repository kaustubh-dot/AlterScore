import { useState } from "react";

const NEGATIVE_CONSTRAINED_FEATURES = new Set([
  "answer_change_rate",
  "dropout_count",
  "scroll_hesitation_score",
  "delay_discounting_rate",
  "risk_consistency_flag"
]);

const POSITIVE_CONSTRAINED_FEATURES = new Set([
  "numeracy_score",
  "CRT_score",
  "financial_literacy_score",
  "future_orientation",
  "locus_of_control",
  "conscientiousness_score",
  "social_capital_score",
  "honesty_score",
  "resilience_score",
  "reciprocity_norm",
  "text_sentiment_compound",
  "text_agency_score",
  "text_problem_solving_flag"
]);

export default function ShapBars({ explanation }) {
  const [expandedFeature, setExpandedFeature] = useState(null);
  const maxFactor = Math.max(...explanation.map((factor) => Math.abs(factor.shap_value)), 0.01);

  const toggleExpand = (feature) => {
    setExpandedFeature(expandedFeature === feature ? null : feature);
  };

  return (
    <section className="result-panel result-animate">
      <div className="panel-heading">
        <p className="eyebrow">SHAP explanation</p>
        <h2>Factors Influencing Your Score</h2>
        <p style={{ color: "var(--soft)", fontSize: "0.8rem", marginTop: "0.2rem" }}>
          Click on any category below to understand its impact and mathematical validation parameters.
        </p>
      </div>
      <div className="shap-list" style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
        {explanation.map((factor) => {
          const positive = factor.direction === "positive";
          const width = Math.max((Math.abs(factor.shap_value) / maxFactor) * 100, 3);
          const isExpanded = expandedFeature === factor.feature;
          const isNegativeConstrained = NEGATIVE_CONSTRAINED_FEATURES.has(factor.feature);
          const isPositiveConstrained = POSITIVE_CONSTRAINED_FEATURES.has(factor.feature);

          return (
            <article 
              className="shap-row" 
              key={`${factor.feature}-${factor.shap_value}`} 
              data-cursor="interactive"
              onClick={() => toggleExpand(factor.feature)}
              style={{
                background: isExpanded ? "rgba(255, 255, 255, 0.02)" : "transparent",
                border: isExpanded ? "1px solid var(--border-active)" : "1px solid transparent",
                borderRadius: "0px",
                padding: "0.8rem 1rem",
                cursor: "pointer",
                transition: "all 0.3s ease",
                display: "flex",
                flexDirection: "column",
                gap: "0.5rem"
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", width: "100%" }}>
                <div style={{ display: "flex", flexDirection: "column" }}>
                  <strong style={{ color: isExpanded ? "var(--accent)" : "var(--text-strong)", fontSize: "0.95rem" }}>
                    {factor.display_name}
                  </strong>
                  <span style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: "0.1rem" }}>
                    {factor.plain_language}
                  </span>
                </div>
                <span className={positive ? "factor-badge is-positive" : "factor-badge is-negative"} style={{
                  padding: "0.25rem 0.5rem",
                  borderRadius: "0px",
                  fontSize: "0.8rem",
                  fontWeight: "bold",
                  background: positive ? "rgba(48,242,210,0.1)" : "rgba(255,77,94,0.1)",
                  color: positive ? "var(--status-excellent)" : "var(--status-poor)"
                }}>
                  {positive ? "+" : "-"} {Math.abs(factor.shap_value).toFixed(2)}
                </span>
              </div>

              <div className="shap-track" style={{ width: "100%", background: "rgba(255,255,255,0.03)", height: "8px", borderRadius: "0px", overflow: "hidden", position: "relative" }}>
                <span
                  className={`shap-fill ${positive ? "is-positive" : "is-negative"}`}
                  style={{ 
                    display: "block",
                    height: "100%",
                    width: `${width}%`,
                    background: positive ? "var(--status-excellent)" : "var(--status-poor)",
                    transition: "width 0.8s ease"
                  }}
                />
              </div>

              {isExpanded && (
                <div 
                  className="shap-detail-drawer" 
                  style={{ 
                    padding: "0.8rem", 
                    marginTop: "0.4rem", 
                    background: "rgba(0,0,0,0.2)", 
                    borderRadius: "0px", 
                    fontSize: "0.8rem", 
                    color: "var(--text-muted)",
                    lineHeight: "1.4",
                    borderLeft: "2px solid var(--accent)"
                  }}
                  onClick={(e) => e.stopPropagation()} // Prevent closing when clicking drawer content
                >
                  <div className="shap-detail-grid">
                    <div>
                      <span className="mono-text" style={{ fontSize: "0.7rem", color: "var(--soft)", display: "block" }}>// FEATURE CODE</span>
                      <strong style={{ fontFamily: "var(--font-mono)", fontSize: "0.75rem" }}>{factor.feature}</strong>
                    </div>
                    <div>
                      <span className="mono-text" style={{ fontSize: "0.7rem", color: "var(--soft)", display: "block" }}>// EVALUATED VALUE</span>
                      <strong>
                        {factor.feature === "avg_response_time_ms"
                          ? `${(factor.feature_value / 1000).toFixed(2)}s`
                          : factor.feature === "session_duration_sec"
                          ? `${factor.feature_value.toFixed(0)}s`
                          : factor.feature === "answer_change_rate"
                          ? `${(factor.feature_value * 100).toFixed(1)}%`
                          : factor.feature === "typing_speed_wpm"
                          ? `${factor.feature_value.toFixed(1)} WPM`
                          : Number.isInteger(factor.feature_value)
                          ? factor.feature_value.toString()
                          : factor.feature_value.toFixed(2)}
                      </strong>
                    </div>
                    <div>
                      <span className="mono-text" style={{ fontSize: "0.7rem", color: "var(--soft)", display: "block" }}>// SHAP IMPACT SCORE</span>
                      <strong>{factor.shap_value > 0 ? "+" : ""}{factor.shap_value.toFixed(4)}</strong>
                    </div>
                  </div>
                  {/* Governance note — only for monotonically constrained features */}
                  {isPositiveConstrained && (
                    <p style={{ margin: "0.5rem 0 0 0", color: "var(--text-muted)" }}>
                      <strong>Governance Note:</strong> This feature has a positive monotonic
                      constraint. Improvements here can only benefit your score — the model is
                      mathematically prevented from penalising you for getting better on this
                      dimension.
                    </p>
                  )}
                  {isNegativeConstrained && (
                    <p style={{ margin: "0.5rem 0 0 0", color: "var(--text-muted)" }}>
                      <strong>Governance Note:</strong> This feature has a negative monotonic
                      constraint. Higher raw values on this signal correspond to lower repayment
                      likelihood — for example, very fast responses or frequent answer changes
                      can indicate low engagement.
                    </p>
                  )}
                </div>
              )}
            </article>
          );
        })}
      </div>
    </section>
  );
}
