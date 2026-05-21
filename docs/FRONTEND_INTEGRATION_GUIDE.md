# Frontend Integration Guide

This guide covers the current frontend contract with the AlterScore backend.

## Backend Base URL

- Local backend: `http://127.0.0.1:8000/api`
- Frontend override: `VITE_API_BASE_URL`

Start the backend before the frontend.

```powershell
# Terminal 1 - backend, from the repository root
backend\.venv-cleanup\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2 - frontend
cd frontend
& 'C:\Program Files\nodejs\npm.cmd' run dev -- --host 127.0.0.1 --port 5173
```

## Verify Backend Health First

Confirm `GET /api/health` before testing borrower flows. A healthy checked-in
bundle should report:

- `status: "ok"`
- `model_loaded: true`
- `manifest_backed: true`
- empty `missing_artifacts`
- empty `invalid_artifacts`

## Score Request Flow

`POST /api/score` is the primary borrower submission path. The frontend sends:

- `session_id`
- `answers`
- `behavioral`

Reference payload: `tests/fixtures/score_request_valid.json`

### Important Answer Notes

- `numeracy_q*` fields are numeric exact-answer prompts.
- `financial_literacy_q*`, `risk_q*`, `loss_aversion_q1`, and repeat fields are
  binary.
- `conscientiousness_q1`, `honesty_trap_q*`, and some resilience/reciprocity
  fields are ordinal.
- `q27_resilience_text` is free text and should stay <=1000 characters.

### Important Behavioral Notes

- `avg_response_time_ms` should be >=0.
- `answer_change_rate` should stay in `0.0-1.0`.
- `session_duration_sec` should be >=0.
- `scroll_hesitation_score` should stay in `0.0-1.0`.
- `risk_response_speed_ratio` should stay in `0.0-5.0`.
- `time_of_day` must be one of `morning`, `afternoon`, `evening`, `night`.
- `device_type` must be one of `mobile`, `desktop`, `tablet`.

## Response Expectations

The score response includes:

- `credit_score`
- `risk_band`
- `repayment_probability`
- `percentile`
- `explanation`
- `counterfactual_actions`
- `loan_eligibility`
- `improvement_tips`
- `timestamp`

## Retry-Safe Submission Rules

1. Keep the same `session_id` on retry.
2. Resubmit the same payload on retry.
3. Do not clear answers on network failure.
4. Handle `503` as backend artifact unavailability, not a client bug.

## Current Frontend Status

Implemented:

- landing page
- assessment flow
- telemetry capture
- score payload construction
- processing screen
- results rendering
- score sharing/export
- dashboard shell

Still pending:

- full dashboard analytics-panel wiring
- deeper frontend test coverage
- final browser QA evidence across target viewports

## Dashboard Endpoints

The dashboard is expected to consume these backend routes independently:

- `/api/model-stats`
- `/api/baseline-comparison`
- `/api/fairness-report`
- `/api/drift-report`
- `/api/global-importance`
- `/api/score-distribution`
- `/api/roc-data`
- `/api/pr-curve`
- `/api/calibration-curve`
- `/api/confusion-matrix`

Each panel should own its own loading, empty, and error states.
