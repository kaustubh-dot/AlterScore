import { QUESTIONS } from "../data/questions.js";

const RISK_BANDS = {
  poor: { label: "Poor", min: 300, max: 499, color: "#ff4d5e" },
  fair: { label: "Fair", min: 500, max: 599, color: "#ffad33" },
  good: { label: "Good", min: 600, max: 699, color: "#b9f24b" },
  very_good: { label: "Very Good", min: 700, max: 799, color: "#38e6a6" },
  excellent: { label: "Excellent", min: 800, max: 850, color: "#30f2d2" },
};

export function createSessionId() {
  if (window.crypto?.randomUUID) {
    return window.crypto.randomUUID();
  }
  return `session-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export function coerceAnswerValue(question, value) {
  if (question.type === "number") {
    const numberValue = Number(value);
    return Number.isFinite(numberValue) ? numberValue : "";
  }
  if (question.type === "text") {
    return String(value || "").slice(0, question.maxLength || 1000);
  }
  return Number(value);
}

export function buildAnswersPayload(answers) {
  return QUESTIONS.reduce((payload, question) => {
    const value = answers[question.id];
    payload[question.id] = coerceAnswerValue(question, value);
    return payload;
  }, {});
}

export function buildBehavioralPayload({ telemetry, answers, sessionStartTime, submittedAt = Date.now() }) {
  const responseTimes = telemetry.responseTimes;
  const times = Object.values(responseTimes).map(Number).filter((value) => Number.isFinite(value));
  const avgResponseTimeMs = clip(mean(times, 5200), 100, 120000);
  const changedQuestionCount = Object.values(telemetry.changeCounts).filter((count) => count > 0).length;
  const riskTimes = QUESTIONS.filter((question) => question.isRiskQuestion)
    .map((question) => responseTimes[question.id])
    .filter((value) => Number.isFinite(value));

  return {
    avg_response_time_ms: round(avgResponseTimeMs),
    answer_change_rate: round(clip(changedQuestionCount / QUESTIONS.length, 0, 1), 4),
    session_duration_sec: round(clip((submittedAt - sessionStartTime) / 1000, 0, 7200)),
    dropout_count: Math.min(Math.max(telemetry.dropoutCount, 0), 20),
    scroll_hesitation_score: round(
      clip(Object.keys(telemetry.scrollHesitations).length / QUESTIONS.length, 0, 1),
      4,
    ),
    risk_response_speed_ratio: round(clip(mean(riskTimes, avgResponseTimeMs) / avgResponseTimeMs, 0, 5), 4),
    time_of_day: getTimeOfDay(),
    device_type: getDeviceType(),
    typing_speed_wpm: round(clip(computeTypingSpeed(answers.q27_resilience_text, responseTimes.q27_resilience_text), 0, 200)),
  };
}

export function getTimeOfDay(date = new Date()) {
  const hour = date.getHours();
  if (hour >= 5 && hour < 12) return "morning";
  if (hour >= 12 && hour < 17) return "afternoon";
  if (hour >= 17 && hour < 21) return "evening";
  return "night";
}

export function getDeviceType() {
  const width = window.innerWidth;
  if (width < 768) return "mobile";
  if (width < 1100) return "tablet";
  return "desktop";
}

export function computeTypingSpeed(text = "", responseTimeMs = 0) {
  const trimmed = String(text || "").trim();
  if (!trimmed || !responseTimeMs) return 0;
  const minutes = responseTimeMs / 60000;
  const words = Math.max(trimmed.length / 5, trimmed.split(/\s+/).filter(Boolean).length);
  return minutes > 0 ? words / minutes : 0;
}

export function getRiskBand(scoreOrBand) {
  if (typeof scoreOrBand === "string") {
    return RISK_BANDS[scoreOrBand] || RISK_BANDS.fair;
  }
  const score = Number(scoreOrBand);
  if (score >= 800) return RISK_BANDS.excellent;
  if (score >= 700) return RISK_BANDS.very_good;
  if (score >= 600) return RISK_BANDS.good;
  if (score >= 500) return RISK_BANDS.fair;
  return RISK_BANDS.poor;
}

export function formatCurrencyRange(loanEligibility) {
  if (!loanEligibility) return "";
  return `Rs. ${loanEligibility.amount_min.toLocaleString("en-IN")} - Rs. ${loanEligibility.amount_max.toLocaleString("en-IN")}`;
}

function mean(values, fallback = 0) {
  if (!values.length) return fallback;
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function clip(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

function round(value, places = 2) {
  const factor = 10 ** places;
  return Math.round(value * factor) / factor;
}
