import { useEffect, useState } from "react";

const statuses = [
  "Processing behavioral signals...",
  "Running gradient boosting model...",
  "Running neural network...",
  "Running logistic regression...",
  "Stacking ensemble predictions...",
  "Generating SHAP explanations...",
  "Computing counterfactuals...",
  "Ranking against applicant pool...",
  "Score ready.",
];

export default function ProcessingScreen() {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const interval = window.setInterval(() => {
      setIndex((value) => Math.min(value + 1, statuses.length - 1));
    }, 900);
    return () => window.clearInterval(interval);
  }, []);

  return (
    <div className="processing-screen">
      <div className="processing-flash" />
      <div className="processing-core">
        <h1>ANALYZING</h1>
        <p>&gt; {statuses[index]}</p>
      </div>
    </div>
  );
}
