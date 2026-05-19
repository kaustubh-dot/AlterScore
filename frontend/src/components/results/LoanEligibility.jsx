import { formatCurrencyRange } from "../../services/scorePayload.js";

export default function LoanEligibility({ eligibility }) {
  return (
    <div className="result-panel">
      <div className="panel-heading">
        <p className="eyebrow">Loan eligibility</p>
        <h2>{formatCurrencyRange(eligibility)}</h2>
      </div>
      <div className="eligibility-track">
        <span />
        <i style={{ left: "18%" }}>₹{eligibility.amount_min.toLocaleString("en-IN")}</i>
        <i style={{ left: "78%" }}>₹{eligibility.amount_max.toLocaleString("en-IN")}</i>
      </div>
      <p className="eligibility-copy">{eligibility.description}</p>
    </div>
  );
}
