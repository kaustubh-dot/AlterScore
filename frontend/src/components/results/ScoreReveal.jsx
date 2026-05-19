import { Suspense, lazy } from "react";

const GaugeArc = lazy(() => import("../webgl/GaugeArc.jsx"));

export default function ScoreReveal({ result, displayScore, dynamicColor, bandMeta }) {
  return (
    <div className="score-stage">
      <Suspense fallback={null}>
        <GaugeArc score={result.credit_score} />
      </Suspense>
      <div className="score-number" style={{ color: dynamicColor }}>
        {displayScore}
      </div>
      <div className="risk-pill result-animate" style={{ "--pill-color": bandMeta.color }}>
        {bandMeta.label}
      </div>
      <p className="percentile-line result-animate">
        Better than <strong>{result.percentile}%</strong> of applicants
      </p>
      <p className="probability-line result-animate">
        Estimated repayment likelihood: {Math.round(result.repayment_probability * 100)}%
      </p>
    </div>
  );
}
