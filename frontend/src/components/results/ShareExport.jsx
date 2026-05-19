import { Link } from "react-router-dom";

export default function ShareExport({ downloadCertificate, shareResults }) {
  return (
    <div className="result-actions result-animate">
      <button type="button" onClick={downloadCertificate} data-magnetic>
        Download certificate
      </button>
      <button type="button" onClick={shareResults} data-magnetic>
        Share results
      </button>
      <Link to="/assessment" data-magnetic>
        Run again
      </Link>
    </div>
  );
}
