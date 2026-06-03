import { useEffect, useState } from "react";

import { useVisualExperience } from "../../context/VisualExperienceContext.jsx";

const checkSteps = [
  "Validating your responses",
  "Reading behavioral context",
  "Running the governed score model",
  "Building your explanation",
  "Mapping practical next steps",
];

export default function ProcessingScreen() {
  const [currentStep, setCurrentStep] = useState(0);
  const { setMode, setProcessingIntensity } = useVisualExperience();

  useEffect(() => {
    setMode("processing");
    const timer = window.setInterval(() => {
      setCurrentStep((value) => {
        if (value >= checkSteps.length) {
          window.clearInterval(timer);
          return value;
        }
        return value + 1;
      });
    }, 940);
    return () => {
      window.clearInterval(timer);
      setMode("assessment");
      setProcessingIntensity(0);
    };
  }, [setMode, setProcessingIntensity]);

  useEffect(() => {
    setProcessingIntensity(Math.min(1, currentStep / checkSteps.length));
  }, [currentStep, setProcessingIntensity]);

  const activeStep = Math.min(currentStep, checkSteps.length - 1);

  return (
    <div className="processing-screen">
      <div className="processing-copy">
        <p>AlterScore / governed analysis</p>
        <h1>Building your fuller picture.</h1>
        <span>{checkSteps[activeStep]}</span>
        <div className="processing-progress">
          <i style={{ transform: `scaleX(${Math.min(1, (currentStep + 1) / checkSteps.length)})` }} />
        </div>
        <ol>
          {checkSteps.map((step, index) => (
            <li className={index < currentStep ? "is-done" : index === activeStep ? "is-active" : ""} key={step}>
              <b>{String(index + 1).padStart(2, "0")}</b>
              <span>{step}</span>
            </li>
          ))}
        </ol>
      </div>
    </div>
  );
}
