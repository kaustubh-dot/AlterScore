# AlterScore: Frontend-to-Backend Handoff Guide

This document acts as the technical handoff guide for developers, mapping API schemas, telemetry payload fields, and boundary constraints between the React client and the scoring engine.

---

## 1. Score Request Contract (`ScoreRequest`)

The client POSTs scoring payloads to the `/api/v1/score` endpoint. The payload is divided into `answers` and `behavioral` groups:

### Answers Payload Schema (`AnswerPayload`)
Contains 27 psychometric responses, 4 traps, and 1 text field. Reference values:
* **numeracy_q1**: `int` (0 to 10,000) — Correct: `6600`
* **numeracy_q2**: `float` (0 to 10,000) — Correct: `1120.0`
* **numeracy_q3**: `float` (0 to 100,000) — Correct: `14400.0`
* **financial_literacy_q1**: `int` (0 to 3) — Correct index: `1`
* **financial_literacy_q2**: `int` (0 to 2) — Correct index: `1`
* **CRT_q1**: `float` (0 to 1000) — Correct: `5.0`
* **CRT_q2**: `float` (0 to 1000) — Correct: `5.0`
* **CRT_q3**: `int` (1 to 48) — Correct: `47`
* **future_orient_q1**, **future_orient_q2**: `int` (0 or 1) — Binary selections
* **future_orient_q3**, **locus_q3**, **conscientiousness_q1**, **resilience_q1**, **resilience_q2**, **reciprocity_q1**: `int` (1 to 5) — Likert scale values (1: Strongly Disagree, 5: Strongly Agree)
* **risk_q1**, **risk_q2**: `int` (0 or 1) — Risk preference selections
* **locus_q1**, **locus_q2**: `int` (0 to 2) — Locus selections
* **social_capital_q1**: `int` (0 to 3), **social_capital_q2**, **social_capital_q3**: `int` (0 to 2) — Network metrics
* **resilience_q3**: `int` (0 to 3), **loss_aversion_q1**: `int` (0 to 2)
* **future_orient_repeat**: `int` (0 or 1), **locus_repeat**: `int` (0 to 2) — Repeat consistency checks
* **honesty_trap_q1**, **honesty_trap_q2**: `int` (1 to 5) — Likert scale trap indicators
* **q27_resilience_text**: `str` (minimum 10 words, maximum 1000 characters)

### Telemetry Payload Schema (`BehavioralPayload`)
Aggregated client-side behavior sent to the ML engine:
* `avg_response_time_ms`: `float` (100.0 to 120,000.0) — Sum of question view durations divided by 27.
* `answer_change_rate`: `float` (0.0 to 1.0) — Proportion of questions where the user changed their mind.
* `session_duration_sec`: `float` (0.0 to 7200.0) — Total duration from test start to submission.
* `dropout_count`: `int` (0 to 20) — Count of window focus loss events.
* `scroll_hesitation_score`: `float` (0.0 to 1.0) — Ratio of questions with scroll direction swaps.
* `risk_response_speed_ratio`: `float` (0.0 to 5.0) — Response speed on risk cards divided by the overall average.
* `time_of_day`: `str` (`"morning"`, `"afternoon"`, `"evening"`, `"night"`)
* `device_type`: `str` (`"mobile"`, `"desktop"`, `"tablet"`)
* `typing_speed_wpm`: `float` (0.0 to 200.0) — WPM calculation on Question 27.

---

## 2. Calibrated Score Response Schema (`ScoreResponse`)

The backend returns a standard JSON structure upon scoring success. Note that our recalibrated score mapping uses a wider logistic scaling factor (`63.2`) to eliminate high-end score saturation, meaning that Excellent ratings (up to 850) are highly descriptive and granular:

```json
{
  "session_id": "uuid-string",
  "credit_score": 765,
  "risk_band": "excellent",
  "repayment_probability": 0.9422,
  "percentile": 82,
  "explanation": [
    {
      "feature": "numeracy_score",
      "display_name": "Financial Math Accuracy",
      "shap_value": 0.3820,
      "direction": "positive",
      "feature_value": 1.0,
      "plain_language": "Financial Math Accuracy is supporting the current score."
    }
  ],
  "counterfactual_actions": [
    {
      "feature": "future_orientation",
      "current_value": 0.0,
      "suggested_value": 1.0,
      "estimated_score_gain": 18,
      "plain_language": "Wait longer for better outcomes to show future planning."
    }
  ],
  "loan_eligibility": {
    "band": "excellent",
    "amount_min": 30000,
    "amount_max": 75000,
    "description": "Eligible for larger starter microloans..."
  },
  "improvement_tips": [
    {
      "feature": "conscientiousness_score",
      "title": "Build repayment habits",
      "body": "Small routines around planning..."
    }
  ],
  "timestamp": "2026-05-23T08:16:13.123Z"
}
```

---

## 3. Telemetry Integrity: U-Shaped Pacing & Text Checks

The backend now enforces strict **behavioral anti-gaming filters** that the frontend must align with:

1. **U-Shaped Response Pacing**:
   * *Optimal Pace*: Spend 4–15 seconds per question card.
   * *Fast Pacing Penalty*: Completing the quiz extremely fast ($t < 4000\text{ms}$ per question) or finishing the session in under $120\text{ seconds}$ will quadratically inflate the pacing parameters inside the backend. This triggers the XGBoost negative monotonic constraints, dropping the final score.
   * **Guidance**: Frontend should naturally slow down or nudge the user if they click through choices too fast.
2. **Text Quality Validation**:
   * *Audit Criteria*: Word count must be $\ge 10$ words. Lexical diversity ratio ($\text{Unique Words} / \text{Total Words}$) must be $\ge 0.60$. Text must not contain repeated spam characters (e.g. keyboard mashes) making up $>35\%$ of the total length.
   * *Anomalous Input Penalty*: Failing these filters sets Spacy/VADER features to maximum negative targets, applying strict score penalties.
   * **Guidance**: Frontend must validate character and word repetition in real time on Question 27, prompting the applicant with helpful guidelines to "explain their actions clearly."
3. **Copy-Paste and Bot Detection**:
   * *Typing Speed Audit*: Copy-pasting responses or using automated script typing yields WPM $>85.0$. The backend reverses this to $0.0\text{ WPM}$, stripping away positive score contributions.
   * **Guidance**: Frontend should discourage copy-pasting into the textarea or log a clipboard paste event.

---

## 4. Environment & Configuration Variables

Ensure the following configuration variables are loaded in the environment (`.env.production`):
* `VITE_API_URL`: The base domain for backend requests (e.g. `https://api.alterscore.io`).
* `VITE_TELEMETRY_LOGGING`: Set to `true` to enable tracking behaviors.
* `VITE_DEMO_PRESETS`: Enable to inject pre-populated test data (like the Excellent and Risky personas) during presentation audits.

