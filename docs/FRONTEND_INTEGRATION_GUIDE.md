# Frontend Integration Guide

This guide covers everything a frontend developer needs to integrate with the AlterScore backend API. The backend is stable, manifest-backed, and fully tested. Do not modify backend code without reading `docs/ENGINEERING_CONTEXT.md` and `docs/DECISIONS.md` first.

## Backend Base URL

```
Local development: http://localhost:8000/api
Frontend Vite proxy target: see VITE_API_BASE_URL in .env
```

Start the backend before the frontend:

```powershell
# Terminal 1 — Backend
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2 — Frontend
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

## Verify Backend Health First

Before building any frontend feature, confirm the backend is serving:

```
GET /api/health
```

A healthy response includes:

```json
{
  "status": "ok",
  "model_loaded": true,
  "manifest_backed": true,
  "manifest_version": "local_logistic_runtime_bundle_v1",
  "model_version": "0.1.0",
  "artifacts_loaded": ["runtime_model", "preprocessor", "shap_explainer", "dice_explainer", "..."],
  "missing_artifacts": [],
  "invalid_artifacts": []
}
```

If `model_loaded` is `false`, the scoring endpoint will return `503`. Fix the backend before continuing.

---

## Score Request Flow (`POST /api/score`)

This is the core borrower integration. The frontend submits assessment answers plus behavioral telemetry and receives a full score response.

### Request Payload

```json
{
  "session_id": "optional-uuid-generated-by-frontend",
  "answers": {
    "numeracy_q1": 6600,
    "numeracy_q2": 1120,
    "numeracy_q3": 14400,
    "financial_literacy_q1": 1,
    "financial_literacy_q2": 1,
    "conscientiousness_q1": 4,
    "CRT_q1": 5,
    "CRT_q2": 5,
    "CRT_q3": 47,
    "future_orient_q1": 1,
    "future_orient_q2": 1,
    "future_orient_q3": 4,
    "risk_q1": 0,
    "risk_q2": 1,
    "locus_q1": 0,
    "locus_q2": 1,
    "locus_q3": 4,
    "social_capital_q1": 2,
    "social_capital_q2": 0,
    "social_capital_q3": 0,
    "resilience_q1": 4,
    "resilience_q2": 4,
    "resilience_q3": 0,
    "loss_aversion_q1": 0,
    "honesty_trap_q1": 2,
    "honesty_trap_q2": 3,
    "future_orient_repeat": 1,
    "locus_repeat": 0,
    "reciprocity_q1": 4,
    "reciprocity_q2": 0,
    "q27_resilience_text": "When my income fell, I reduced expenses."
  },
  "behavioral": {
    "avg_response_time_ms": 5200.0,
    "answer_change_rate": 0.08,
    "session_duration_sec": 410.0,
    "dropout_count": 0,
    "scroll_hesitation_score": 0.52,
    "risk_response_speed_ratio": 0.85,
    "time_of_day": "afternoon",
    "device_type": "mobile",
    "typing_speed_wpm": 34.0
  }
}
```

### Answer Field Types

| Field Pattern | Type | Constraints |
|---|---|---|
| `numeracy_q*` | Number | PRD-specified correct answers: 6600, 1120, 14400 |
| `financial_literacy_q*` | Integer 0-1 | Binary true/false |
| `conscientiousness_q1` | Integer 1-5 | Likert scale |
| `CRT_q*` | Number | Exact answer (trap: 10, 100, 24 → system detects) |
| `future_orient_q*` | Integer 0-1 or 1-5 | Mixed (q1/q2 binary, q3 Likert) |
| `risk_q*` | Integer 0-1 | Binary gamble choice |
| `locus_q*` | Integer 0-1 or 1-5 | Mixed |
| `social_capital_q*` | Integer 0-2 | Count or ordinal |
| `resilience_q*` | Integer 0-4 or 1-5 | Range depends on question |
| `loss_aversion_q1` | Integer 0-1 | Binary |
| `honesty_trap_q*` | Integer 1-5 | Likert agreement scale |
| `future_orient_repeat` | Integer 0-1 | Consistency check |
| `locus_repeat` | Integer 0-1 | Consistency check |
| `reciprocity_q*` | Integer 0-4 or 1-5 | Ordinal |
| `q27_resilience_text` | String ≤1000 chars | Open text, empty allowed |

### Behavioral Telemetry Fields

All behavioral fields are collected automatically by the frontend during the assessment session.

| Field | Type | Constraints | How To Capture |
|---|---|---|---|
| `avg_response_time_ms` | Float | ≥0, clip to 60000 | Mean time between question transitions |
| `answer_change_rate` | Float | 0.0–1.0 | Count of changed answers ÷ total questions |
| `session_duration_sec` | Float | ≥0, clip to 3600 | `Date.now()` at submit minus session start |
| `dropout_count` | Integer | ≥0 | Number of times user navigated away |
| `scroll_hesitation_score` | Float | 0.0–1.0 | Fraction of questions where scroll paused >3s |
| `risk_response_speed_ratio` | Float | 0.0–5.0 | Risk question time ÷ average question time |
| `time_of_day` | String | `morning`, `afternoon`, `evening`, `night` | Map current hour |
| `device_type` | String | `mobile`, `desktop`, `tablet` | Media query or user agent |
| `typing_speed_wpm` | Float | ≥0, clip to 200 | Character count of Q27 text ÷ typing duration ÷ 5 |

**Critical:** `time_of_day` and `device_type` must be one of the documented values. Any other value returns a `422` validation error.

### Response Payload

```json
{
  "session_id": "uuid",
  "credit_score": 712,
  "risk_band": "good",
  "repayment_probability": 0.7314,
  "percentile": 68,
  "explanation": [
    {
      "feature": "future_orientation",
      "display_name": "Future Orientation",
      "shap_value": 0.082,
      "direction": "positive",
      "feature_value": 0.91,
      "plain_language": "Future-oriented choices increased the score."
    }
  ],
  "counterfactual_actions": [
    {
      "feature": "numeracy_score",
      "current_value": 0.66,
      "suggested_value": 0.85,
      "estimated_score_gain": 24,
      "plain_language": "Improving financial math accuracy could move the score upward."
    }
  ],
  "loan_eligibility": {
    "band": "good",
    "amount_min": 10000,
    "amount_max": 30000,
    "description": "Eligible for a moderate starter loan subject to lender policy."
  },
  "improvement_tips": [
    {
      "feature": "numeracy_score",
      "title": "Strengthen financial math",
      "body": "Practice interest, discount, and savings calculations before applying again."
    }
  ],
  "model_version": "0.1.0",
  "model_name": "logistic_regression",
  "timestamp": "2026-05-16T07:00:00Z"
}
```

### Retry-Safe Submission

The scoring endpoint is stateless and idempotent for the same payload. Implement this pattern:

1. Capture all answers and telemetry in local state before submission.
2. On network failure, show a retry button that resubmits the **same** payload.
3. Do NOT regenerate `session_id` on retry — use the same one.
4. Never clear the user's answers on failure.
5. Show a loading spinner during the request (typical latency: 200–800ms).

### Error Handling

| Status | Meaning | Frontend Action |
|---|---|---|
| 200 | Success | Navigate to results page with response data |
| 422 | Validation error | Show field-level errors from `detail` array |
| 500 | Internal server error | Show "Something went wrong, please try again" with retry |
| 503 | Artifacts not loaded | Show "Service temporarily unavailable" — backend needs restart |

---

## Score Rendering Guidance

### Score Gauge

- Score range: always 300–850
- Risk bands: `poor` (300–499), `fair` (500–599), `good` (600–699), `very_good` (700–799), `excellent` (800–850)
- Render as a semicircular gauge, speedometer, or arc chart
- Color-code by risk band: red → orange → yellow → green → dark green
- Show the numeric score prominently with the risk band label below

### Percentile

- Display as "Better than X% of applicants"
- Range: 0–100
- Consider a small bar or indicator alongside the score

### Repayment Probability

- This is the raw model output (0.0–1.0)
- Can be displayed as "X% estimated repayment likelihood" if appropriate
- Some designs hide this from borrowers and show only the score/band

---

## SHAP Explanation Rendering

The `explanation` array contains up to 6 SHAP factor items, sorted by absolute magnitude.

### Rendering Pattern

- Render as horizontal bars (positive=green going right, negative=red going left)
- Use `display_name` as the label (human-readable)
- Use `plain_language` as a tooltip or subtitle
- Show `direction` as an icon: ↑ for positive, ↓ for negative
- The `shap_value` determines bar width (normalize to the max value in the list)
- The `feature_value` can be shown as context but is not required for the visual

### Edge Cases

- `explanation` may be empty if the SHAP artifact is missing — show "Explanations not available"
- All values may be small — still render them, they represent relative importance

---

## DICE Counterfactual Action Rendering

The `counterfactual_actions` array contains 0–3 actionable improvement suggestions.

### Rendering Pattern

- Render as cards with an action title derived from `plain_language`
- Show `estimated_score_gain` as "+X points" badge
- Do NOT show raw `feature` names to borrowers — use `plain_language` only
- If `estimated_score_gain` is 0, the action still improves repayment probability

### Edge Cases

- Array may be empty for very high scorers — show "No improvements suggested"
- Actions never suggest changing protected attributes (age, gender, region, education)

---

## Loan Eligibility Rendering

- Always present in the response
- Show `loan_eligibility.description` as the primary text
- Show amount range as "₹{amount_min} – ₹{amount_max}" if applicable
- Color-code by band following the same risk-band palette

---

## Analytics Dashboard Endpoints

All analytics endpoints are `GET` requests that return pre-computed report data. They do NOT trigger model inference.

| Endpoint | Use For |
|---|---|
| `/api/model-stats` | Model metrics table (AUC, precision, recall, etc.) |
| `/api/baseline-comparison` | Comparison vs loan officer and majority classifier |
| `/api/fairness-report` | Subgroup fairness audit panel |
| `/api/drift-report` | Feature drift (PSI) panel |
| `/api/global-importance` | Feature importance bar chart |
| `/api/score-distribution` | Score histogram |
| `/api/roc-data` | ROC curve chart |
| `/api/pr-curve` | Precision-recall curve chart |
| `/api/calibration-curve` | Calibration curve chart |
| `/api/confusion-matrix` | Confusion matrix visualization |

### Dashboard Error Handling

- Each panel should fetch independently
- If one endpoint returns `503` (report missing), show "Data not available" in that panel
- Never let one failed panel crash the entire dashboard
- Show loading spinners per panel, not a single global spinner

---

## Mobile / Responsive Considerations

- Assessment flow must work at 375px width
- Questions should be single-column on mobile
- Score gauge should resize responsively
- Dashboard charts should scroll horizontally if they can't fit at 375px
- Tables should use horizontal scroll containers on mobile
- Touch targets must be ≥44px

---

## Frontend Testing Recommendations

### Unit Tests

- Test question data completeness (all 27 questions defined)
- Test telemetry computation functions
- Test score request payload construction
- Test risk band color mapping

### Integration Tests

- Test full assessment flow to submission
- Test results page rendering with mock API response
- Test dashboard panel loading with mock data
- Test error states for each panel

### E2E Tests

- Complete assessment → submit → results page with real backend
- Dashboard loads all panels from real backend
- Mobile viewport (375px) renders without overflow

### Test Fixture

Use `tests/fixtures/score_request_valid.json` as the reference payload for backend contract testing.
