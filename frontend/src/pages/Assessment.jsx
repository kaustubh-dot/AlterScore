import { gsap } from "gsap";
import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

import OptionCard from "../components/assessment/OptionCard.jsx";
import ProgressDots from "../components/assessment/ProgressDots.jsx";
import TelemetryOptIn from "../components/assessment/TelemetryOptIn.jsx";
import ProcessingScreen from "../components/processing/ProcessingScreen.jsx";
import { QUESTIONS, getSectionById } from "../data/questions.js";
import { submitScore } from "../services/api.js";
import {
  buildAnswersPayload,
  buildBehavioralPayload,
  createSessionId,
  coerceAnswerValue,
} from "../services/scorePayload.js";

const storedSessionId = window.sessionStorage.getItem("alterscore_session_id") || createSessionId();
window.sessionStorage.setItem("alterscore_session_id", storedSessionId);

const choiceTypes = new Set(["mcq", "binary_choice", "likert"]);

function wait(ms) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

export default function Assessment() {
  const navigate = useNavigate();
  const questionRef = useRef(null);
  const autoTimerRef = useRef(0);
  const pendingPayloadRef = useRef(null);
  const lastScrollY = useRef(window.scrollY);
  const scrollDirection = useRef(0);

  const [consented, setConsented] = useState(() => {
    return window.sessionStorage.getItem("alterscore_telemetry_consented") === "true";
  });
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState(() => {
    try {
      return JSON.parse(window.sessionStorage.getItem("alterscore_answers") || "{}");
    } catch {
      return {};
    }
  });
  const [telemetry, setTelemetry] = useState({
    responseTimes: {},
    changeCounts: {},
    dropoutCount: 0,
    scrollHesitations: {},
  });
  const [questionStartTime, setQuestionStartTime] = useState(Date.now());
  const [sessionStartTime] = useState(Date.now());
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [halfwayPulse, setHalfwayPulse] = useState(false);

  useEffect(() => {
    const storedResult = window.sessionStorage.getItem("alterscore_score_result");
    if (storedResult) {
      navigate("/results", { replace: true });
    }
  }, [navigate]);

  const question = QUESTIONS[currentIndex];
  const currentSection = getSectionById(question.section);
  const isFirst = currentIndex === 0;
  const isLast = currentIndex === QUESTIONS.length - 1;
  const progressLabel = `${currentSection.title.toUpperCase()} · Q${currentIndex + 1} OF ${QUESTIONS.length}`;

  const hasAnswer = useMemo(() => {
    const value = answers[question.id];
    if (question.type === "text") {
      return String(value || "").trim().split(/\s+/).filter(Boolean).length >= (question.minWords || 10);
    }
    return value !== undefined && value !== null && value !== "";
  }, [answers, question]);

  useEffect(() => {
    if (!consented) return;
    setQuestionStartTime(Date.now());
    window.clearTimeout(autoTimerRef.current);
    gsap.fromTo(
      questionRef.current,
      { autoAlpha: 0, x: 80, filter: "blur(8px)" },
      { autoAlpha: 1, x: 0, filter: "blur(0px)", duration: 0.55, ease: "power3.out" },
    );

    if (currentIndex === Math.floor(QUESTIONS.length / 2)) {
      setHalfwayPulse(true);
      const timer = window.setTimeout(() => setHalfwayPulse(false), 1500);
      return () => window.clearTimeout(timer);
    }
    return undefined;
  }, [currentIndex, consented]);

  useEffect(() => {
    window.sessionStorage.setItem("alterscore_answers", JSON.stringify(answers));
  }, [answers]);

  useEffect(() => {
    if (!consented) return;
    const handleVisibility = () => {
      if (document.hidden) {
        setTelemetry((state) => ({ ...state, dropoutCount: Math.min(state.dropoutCount + 1, 20) }));
      }
    };

    const handleScroll = () => {
      const y = window.scrollY;
      const nextDirection = Math.sign(y - lastScrollY.current);
      if (scrollDirection.current && nextDirection && scrollDirection.current !== nextDirection) {
        setTelemetry((state) => ({
          ...state,
          scrollHesitations: { ...state.scrollHesitations, [question.id]: true },
        }));
      }
      scrollDirection.current = nextDirection || scrollDirection.current;
      lastScrollY.current = y;
    };

    document.addEventListener("visibilitychange", handleVisibility);
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => {
      document.removeEventListener("visibilitychange", handleVisibility);
      window.removeEventListener("scroll", handleScroll);
    };
  }, [question.id, consented]);

  // Keyboard Navigation Helpers
  useEffect(() => {
    if (!consented || isSubmitting) return;

    const handleKeyDown = (event) => {
      const activeElement = document.activeElement;
      if (activeElement && (activeElement.tagName === "INPUT" || activeElement.tagName === "TEXTAREA")) {
        // Allow normal typing inside writing questions
        return;
      }

      if (question.type === "likert") {
        const num = Number(event.key);
        if (num >= 1 && num <= 5) {
          recordAnswer(num);
        }
      } else if (question.type === "binary_choice") {
        if (event.key === "1") {
          recordAnswer(0);
        } else if (event.key === "2") {
          recordAnswer(1);
        }
      } else if (question.type === "mcq") {
        const num = Number(event.key);
        const optionsCount = question.options?.length || 0;
        if (num >= 1 && num <= optionsCount) {
          recordAnswer(num - 1);
        }
      }

      if (event.key === "ArrowLeft" || event.key === "Backspace") {
        goBack();
      } else if (event.key === "ArrowRight" || (event.key === "Enter" && hasAnswer)) {
        goForward(false);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [consented, currentIndex, hasAnswer, question, isSubmitting]);

  function recordAnswer(rawValue) {
    const value = coerceAnswerValue(question, rawValue);
    const responseTime = Date.now() - questionStartTime;

    setAnswers((state) => ({ ...state, [question.id]: value }));
    setTelemetry((state) => ({
      ...state,
      responseTimes: { ...state.responseTimes, [question.id]: responseTime },
      changeCounts: {
        ...state.changeCounts,
        [question.id]:
          answers[question.id] !== undefined && answers[question.id] !== value
            ? (state.changeCounts[question.id] || 0) + 1
            : state.changeCounts[question.id] || 0,
      },
    }));

    if (choiceTypes.has(question.type)) {
      window.clearTimeout(autoTimerRef.current);
      autoTimerRef.current = window.setTimeout(() => {
        if (isLast) {
          handleSubmit({ ...answers, [question.id]: value });
        } else {
          goForward(true);
        }
      }, 600);
    }
  }

  function goForward(fromAuto = false) {
    if (!fromAuto && !hasAnswer) return;
    if (isLast) {
      handleSubmit(answers);
      return;
    }

    gsap.to(questionRef.current, {
      autoAlpha: 0,
      x: -60,
      filter: "blur(8px)",
      duration: 0.4,
      ease: "power2.inOut",
      onComplete: () => setCurrentIndex((value) => value + 1),
    });
  }

  function goBack() {
    if (isFirst || isSubmitting) return;
    window.clearTimeout(autoTimerRef.current);
    gsap.to(questionRef.current, {
      autoAlpha: 0,
      x: 70,
      filter: "blur(8px)",
      duration: 0.35,
      ease: "power2.inOut",
      onComplete: () => setCurrentIndex((value) => value - 1),
    });
  }

  function handleStartOver() {
    if (window.confirm("Are you sure you want to start over? All your current progress will be lost.")) {
      window.sessionStorage.removeItem("alterscore_answers");
      window.sessionStorage.removeItem("alterscore_session_id");
      window.sessionStorage.removeItem("alterscore_score_result");
      window.sessionStorage.removeItem("alterscore_pending_payload");
      
      const newSessionId = createSessionId();
      window.sessionStorage.setItem("alterscore_session_id", newSessionId);
      
      setAnswers({});
      setCurrentIndex(0);
      setTelemetry({
        responseTimes: {},
        changeCounts: {},
        dropoutCount: 0,
        scrollHesitations: {},
      });
      setQuestionStartTime(Date.now());
    }
  }

  async function handleSubmit(nextAnswers = answers) {
    let payload = pendingPayloadRef.current;
    if (!payload) {
      const storedPayload = window.sessionStorage.getItem("alterscore_pending_payload");
      if (storedPayload) {
        try {
          payload = JSON.parse(storedPayload);
        } catch {
          payload = null;
        }
      }
    }

    if (!payload) {
      payload = {
        session_id: storedSessionId,
        answers: buildAnswersPayload(nextAnswers),
        behavioral: buildBehavioralPayload({ telemetry, answers: nextAnswers, sessionStartTime }),
      };
    }

    pendingPayloadRef.current = payload;
    window.sessionStorage.setItem("alterscore_pending_payload", JSON.stringify(payload));
    setIsSubmitting(true);
    setError(null);

    try {
      const startedAt = Date.now();
      const result = await submitScore(payload);
      await wait(Math.max(0, 5000 - (Date.now() - startedAt)));
      window.sessionStorage.setItem("alterscore_score_result", JSON.stringify(result));
      pendingPayloadRef.current = null;
      window.sessionStorage.removeItem("alterscore_pending_payload");
      navigate("/results", { state: result });
    } catch (err) {
      setError(err.status === 422 ? "The score contract rejected one field. Your answers are still saved." : "Network failed. Retry will reuse the same payload.");
      setIsSubmitting(false);
    }
  }

  function renderAnswerControl() {
    if (question.type === "number") {
      return (
        <div className="number-answer">
          {question.prefix && <span>{question.prefix}</span>}
          <input
            type="number"
            inputMode="decimal"
            min="0"
            value={answers[question.id] ?? ""}
            onChange={(event) => recordAnswer(event.target.value)}
            placeholder="0"
            autoFocus
          />
          {question.suffix && <span>{question.suffix}</span>}
        </div>
      );
    }

    if (question.type === "text") {
      const wordsCount = String(answers[question.id] || "").trim().split(/\s+/).filter(Boolean).length;
      const minWords = question.minWords || 10;
      const progressPercent = Math.min((wordsCount / minWords) * 100, 100);
      const metMin = wordsCount >= minWords;

      return (
        <div className="open-answer">
          <textarea
            rows={6}
            maxLength={question.maxLength || 1000}
            value={answers[question.id] ?? ""}
            onChange={(event) => recordAnswer(event.target.value)}
            placeholder="Write the moment, the action, and what changed after it."
            style={{
              width: "100%",
              padding: "1rem",
              background: "rgba(255,255,255,0.02)",
              border: "1px solid var(--line)",
              borderRadius: "6px",
              color: "var(--text-strong)",
              fontSize: "1rem",
              lineHeight: "1.6",
              outline: "none",
              transition: "border-color 0.2s"
            }}
          />
          
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "0.5rem", fontSize: "0.8rem" }}>
            <span style={{ color: metMin ? "var(--accent-green)" : "var(--accent-red)", fontWeight: "500" }}>
              {wordsCount} words {metMin ? "✓ Minimum met" : `(needs at least ${minWords} words)`}
            </span>
            <span style={{ color: "var(--soft)" }}>
              Max {question.maxLength || 1000} characters
            </span>
          </div>

          <div style={{ width: "100%", height: "4px", background: "rgba(255,255,255,0.05)", borderRadius: "2px", marginTop: "0.5rem", overflow: "hidden" }}>
            <div style={{
              width: `${progressPercent}%`,
              height: "100%",
              background: metMin ? "var(--accent-green)" : "var(--accent-red)",
              transition: "width 0.3s ease, background-color 0.3s ease"
            }} />
          </div>

          <div className="resilience-helper-card" style={{
            marginTop: "1.5rem",
            padding: "1rem",
            background: "rgba(255,255,255,0.02)",
            borderLeft: "2px solid var(--accent)",
            borderRadius: "0",
            fontSize: "0.85rem",
            lineHeight: "1.5",
            color: "var(--text-muted)"
          }}>
            <strong>Suggestion guide</strong>
            <ul style={{ margin: "0.5rem 0 0 0", paddingLeft: "1.2rem" }}>
              <li>What was the specific event or challenge? (e.g. startup, business trial, financial plan)</li>
              <li>What did you plan or design as an adjustment?</li>
              <li>What concrete actions did you execute to resolve the conflict?</li>
            </ul>
          </div>
        </div>
      );
    }

    const options = question.type === "likert" ? question.scale : question.options;
    return (
      <div className="answer-options">
        {options.map((option, index) => {
          const value = question.type === "likert" ? index + 1 : index;
          return (
            <OptionCard
              key={`${option}-${index}`}
              selected={Number(answers[question.id]) === value}
              onClick={() => recordAnswer(value)}
            >
              {option}
            </OptionCard>
          );
        })}
      </div>
    );
  }

  if (!consented) {
    return (
      <main className="assessment-experience" data-section style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "80vh" }}>
        <TelemetryOptIn
          onConsent={() => {
            window.sessionStorage.setItem("alterscore_telemetry_consented", "true");
            setConsented(true);
            setQuestionStartTime(Date.now());
          }}
        />
      </main>
    );
  }

  if (isSubmitting) return <ProcessingScreen />;

  return (
    <main className="assessment-experience" data-section>
      <ProgressDots total={QUESTIONS.length} current={currentIndex} />

      {halfwayPulse && (
        <div className="halfway-pulse">
          Halfway there. Your profile is taking shape.
        </div>
      )}

      <section ref={questionRef} className="assessment-question">
        <p className="question-category">{progressLabel}</p>
        <h1>{question.question}</h1>
        {question.hint && <p className="question-hint">{question.hint}</p>}
        {renderAnswerControl()}
        {error && (
          <div className="assessment-error">
            <p>{error}</p>
            <button type="button" onClick={() => handleSubmit(answers)} data-magnetic>
              Retry submission
            </button>
          </div>
        )}
      </section>

      <div className="assessment-controls">
        <div style={{ display: "flex", gap: "0.8rem", pointerEvents: "auto" }}>
          <button type="button" onClick={goBack} disabled={isFirst} data-magnetic>
            Back
          </button>
          {Object.keys(answers).length > 0 && (
            <button
              type="button"
              onClick={handleStartOver}
              data-magnetic
              style={{
                borderColor: "rgba(255, 77, 94, 0.2)",
                color: "var(--text-secondary)",
              }}
            >
              Start over
            </button>
          )}
        </div>
        {!choiceTypes.has(question.type) && (
          <button type="button" onClick={() => goForward(false)} disabled={!hasAnswer} data-magnetic>
            {isLast ? "Submit profile" : "Continue"}
          </button>
        )}
      </div>
    </main>
  );
}
