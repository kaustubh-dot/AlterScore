import { useNavigate } from "react-router-dom";

export default function ShareExport({ downloadCertificate, shareResults }) {
  const navigate = useNavigate();

  const handleRunAgain = () => {
    window.sessionStorage.removeItem("alterscore_answers");
    window.sessionStorage.removeItem("alterscore_session_id");
    window.sessionStorage.removeItem("alterscore_score_result");
    window.sessionStorage.removeItem("alterscore_pending_payload");
    navigate("/assessment");
  };

  return (
    <div className="result-actions result-animate">
      <button type="button" onClick={downloadCertificate} data-magnetic>
        Download certificate
      </button>
      <button type="button" onClick={shareResults} data-magnetic>
        Share results
      </button>
      <button type="button" onClick={handleRunAgain} data-magnetic>
        Run again
      </button>
    </div>
  );
}
