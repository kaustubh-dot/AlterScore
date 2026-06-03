import { gsap } from "gsap";
import html2canvas from "html2canvas";
import { useEffect, useMemo, useRef, useState } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { getRiskBand } from "../services/scorePayload.js";
import { useVisualExperience } from "../context/VisualExperienceContext.jsx";

import ScoreReveal from "../components/results/ScoreReveal.jsx";
import ShapBars from "../components/results/ShapBars.jsx";
import CounterfactualCards from "../components/results/CounterfactualCards.jsx";
import LoanEligibility from "../components/results/LoanEligibility.jsx";
import ImprovementTips from "../components/results/ImprovementTips.jsx";
import ShareExport from "../components/results/ShareExport.jsx";

const colorStops = [
  { score: 300, color: [255, 77, 77] },
  { score: 580, color: [255, 154, 60] },
  { score: 670, color: [245, 197, 24] },
  { score: 740, color: [61, 255, 200] },
  { score: 800, color: [167, 139, 255] },
];

function lerp(start, end, t) {
  return start + (end - start) * t;
}

function scoreToColor(score) {
  const clamped = Math.min(Math.max(Number(score) || 300, 300), 850);
  const stopIndex = colorStops.findIndex((stop) => clamped <= stop.score);
  const upperIndex = stopIndex === -1 ? colorStops.length - 1 : stopIndex;
  const lowerIndex = Math.max(0, upperIndex - 1);
  const lower = colorStops[lowerIndex];
  const upper = colorStops[upperIndex];
  const span = Math.max(upper.score - lower.score, 1);
  const t = Math.min(Math.max((clamped - lower.score) / span, 0), 1);
  const rgb = lower.color.map((value, index) => Math.round(lerp(value, upper.color[index], t)));
  return `rgb(${rgb.join(",")})`;
}

export default function Results() {
  const location = useLocation();
  const { setMode, setScoreTarget } = useVisualExperience();
  const certificateRef = useRef(null);
  const revealRef = useRef(null);
  const [displayScore, setDisplayScore] = useState(300);

  const result = useMemo(() => {
    if (location.state) return location.state;
    try {
      return JSON.parse(window.sessionStorage.getItem("alterscore_score_result") || "null");
    } catch {
      return null;
    }
  }, [location.state]);

  useEffect(() => {
    if (!result) return undefined;
    setMode("results");
    setScoreTarget(result.credit_score);

    const state = { value: 300 };
    const context = gsap.context(() => {
      gsap.set(".result-animate", { autoAlpha: 0, y: 34 });
      gsap.to(".result-line-sweep", { scaleX: 1, duration: 0.5, ease: "power3.out" });
      gsap.to(state, {
        value: result.credit_score,
        duration: 2,
        delay: 0.5,
        ease: "power3.out",
        onUpdate: () => setDisplayScore(Math.round(state.value)),
      });
      gsap.to(".result-animate", {
        autoAlpha: 1,
        y: 0,
        duration: 0.75,
        stagger: 0.12,
        delay: 1.1,
        ease: "power3.out",
      });
      gsap.fromTo(".shap-fill", { scaleX: 0 }, { scaleX: 1, transformOrigin: "left", stagger: 0.08, delay: 2.8, duration: 0.8, ease: "power3.out" });
    }, revealRef);

    return () => {
      context.revert();
      setScoreTarget(null);
    };
  }, [result, setMode, setScoreTarget]);

  if (!result) return <Navigate to="/assessment" replace />;

  const bandMeta = getRiskBand(result.risk_band);
  const dynamicColor = scoreToColor(displayScore);

  async function downloadCertificate() {
    if (!certificateRef.current) return;
    const canvas = await html2canvas(certificateRef.current, { backgroundColor: "#04050F", scale: 2 });
    const link = document.createElement("a");
    link.download = `alterscore-${result.session_id}.png`;
    link.href = canvas.toDataURL("image/png");
    link.click();
  }

  function shareResults() {
    const text = `My AlterScore is ${result.credit_score}, better than ${result.percentile}% of applicants.`;
    if (navigator.share) {
      navigator.share({ title: "AlterScore result", text }).catch(() => {});
      return;
    }
    window.open(`https://wa.me/?text=${encodeURIComponent(text)}`, "_blank", "noopener,noreferrer");
  }

  return (
    <main ref={revealRef} className="results-experience" data-section>
      <div className="result-line-sweep" />

      <section ref={certificateRef} className="results-certificate">
        <ScoreReveal 
          result={result} 
          displayScore={displayScore} 
          dynamicColor={dynamicColor} 
          bandMeta={bandMeta} 
        />

        <ShapBars explanation={result.explanation} />

        <section className="result-grid result-animate">
          <CounterfactualCards actions={result.counterfactual_actions} />
          <LoanEligibility eligibility={result.loan_eligibility} />
        </section>

        <ImprovementTips tips={result.improvement_tips} />
      </section>

      <ShareExport 
        downloadCertificate={downloadCertificate} 
        shareResults={shareResults} 
      />
    </main>
  );
}
