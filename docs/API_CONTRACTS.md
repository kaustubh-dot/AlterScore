# AlterScore API Contracts

## Contract Principles

- Public endpoints must remain compatible with the PRD route list.
- All request and response bodies must have Pydantic schemas.
- Errors must be structured and machine-readable.
- Analytics endpoints should serve generated reports, not recompute expensive training metrics inside request handlers.
- Score responses must never expose protected attributes.

## Base URL

- Local backend: `http://localhost:8000`
- Public PRD API prefix: `/api`
- Internal source organization may use `backend/app/api/v1/routes`.

## Route List

| Method | Path | Purpose | Backing Artifact or Service |
|---|---|---|---|
| GET | `/api/health` | Service and artifact health | Startup artifact cache |
| POST | `/api/score` | Compute score for one assessment | Inference service |
| GET | `/api/model-stats` | Production model metrics | `models/reports/metrics.json` |
| GET | `/api/baseline-comparison` | Baseline and loan-officer comparison | `models/reports/baseline_metrics.json` |
| GET | `/api/fairness-report` | Fairness audit | `models/reports/fairness_report.json` |
| GET | `/api/drift-report` | PSI drift report | `models/reports/psi_report.json` |
| GET | `/api/global-importance` | SHAP global importance | `models/reports/global_importance.json` |
| GET | `/api/score-distribution` | Population score histogram | Population predictions and percentiles |
| GET | `/api/roc-data` | ROC curve points for models | `models/reports/metrics.json` |
| GET | `/api/pr-curve` | Precision-recall curve points | `models/reports/metrics.json` |
| GET | `/api/calibration-curve` | Calibration curve points | `models/reports/metrics.json` |
| GET | `/api/confusion-matrix` | Confusion matrix at optimal threshold | `models/reports/metrics.json` |

## Common Error Response

```json
{
  "error": {
    "code": "SCORING_FAILED",
    "message": "Human readable error",
    "details": {},
    "request_id": "uuid",
    "timestamp": "2026-05-13T00:00:00Z"
  }
}
```

## GET /api/health

Current scaffold note:
- Until the full production bundle exists, the backend may report health from either a manifest-backed bundle or a direct runtime-model fallback used by the scoring stub.
- The checked-in curated bundle currently reports `ok`, while copied or intentionally broken bundles may still report `degraded` even when `model_loaded` is `true` if optional runtime artifacts are missing or invalid but scoring-critical artifacts are present.
- `artifacts_loaded` reflects successful startup load/validation, not just file presence, and `invalid_artifacts` is reserved for present-but-unusable optional artifacts.

### Response

```json
{
  "status": "ok",
  "version": "0.1.0",
  "model_loaded": true,
  "artifacts_loaded": [
    "calibrated_stacking",
    "preprocessor",
    "text_pca",
    "shap_explainer",
    "dice_explainer",
    "metrics",
    "fairness_report",
    "psi_report"
  ],
  "missing_artifacts": [],
  "invalid_artifacts": [],
  "timestamp": "2026-05-13T00:00:00Z"
}
```

## POST /api/score

### Request Body

```json
{
  "session_id": "optional-client-generated-uuid",
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
    "q27_resilience_text": "When my income fell, I reduced expenses, found extra work, and made a repayment plan."
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

### Field Validation

| Field Group | Rules |
|---|---|
| Numeric answer fields | Use PRD min/max bounds in Pydantic schemas |
| Likert fields | Integers 1-5 |
| MCQ fields | Integer option index within the question option range |
| Binary fields | Integer 0 or 1 |
| Q27 text | String, max 1000 characters, empty allowed but receives neutral NLP defaults |
| `time_of_day` | `morning`, `afternoon`, `evening`, `night` |
| `device_type` | `mobile`, `desktop`, `tablet` |

### Response Body

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
  "timestamp": "2026-05-13T00:00:00Z"
}
```

Current scaffold note:
- The response fields above remain required, and the checked-in bundle now returns real `explanation` items when the persisted SHAP artifact loads successfully.
- The checked-in bundle now returns `counterfactual_actions` from the persisted `models/explainers/dice_explainer.pkl` artifact, which stores bounded actionable counterfactual policies against the loaded model bundle and is validated at startup.
- The fallback may legitimately report `estimated_score_gain = 0` when the applicant is already at the current score ceiling but a simulated change still improves repayment probability.
- When `models/preprocessors/text_pca.pkl` is present, runtime semantic dimensions use the persisted PCA artifact; the temporary zero-fill fallback remains only for intentionally PCA-less test or stub bundles.
- Score requests are now append-logged to `runtime/logs/requests.jsonl` by default, without storing the raw answers or behavioral payload in the JSONL entry.
- Structured `500` errors now expose only a sanitized error type in the client payload; full failure details remain in server-side logs.

## GET /api/model-stats

Current foundation note:
- The first analytics endpoint now serves the saved `model_stats` list from `models/reports/metrics.json`.
- If `metrics.json` is missing at startup, the endpoint returns a structured `503` with `missing_artifacts`.

### Response

Uses the `ModelStatsItem` list shape documented below.

## GET /api/baseline-comparison

Current foundation note:
- The second analytics endpoint now serves the saved baseline comparison list from `models/reports/baseline_metrics.json`.
- If `baseline_metrics.json` is missing at startup, the endpoint returns a structured `503` with `missing_artifacts`.

### Response

Uses the `BaselineComparisonItem` list shape documented below.

## GET /api/fairness-report

Current foundation note:
- The fairness endpoint now serves the saved subgroup-audit payload from `models/reports/fairness_report.json`.
- The response is read from the startup-loaded runtime bundle and does not recompute subgroup metrics inside the API process.
- If `fairness_report.json` is missing at startup, the endpoint returns a structured `503` with `missing_artifacts`.

### Response

Uses the `FairnessReport` shape documented below.

## GET /api/drift-report

Current foundation note:
- The drift endpoint now serves the saved PSI payload from `models/reports/psi_report.json`.
- The response is read from the startup-loaded runtime bundle and does not recompute train/test comparisons inside the API process.
- If `psi_report.json` is missing at startup, the endpoint returns a structured `503` with `missing_artifacts`.

### Response

Uses the `DriftReport` shape documented below.

## GET /api/global-importance

Current foundation note:
- The global-importance endpoint now serves the saved dashboard ranking from `models/reports/global_importance.json`.
- The response identifies which saved model produced the ranking so dashboard consumers do not have to infer it from deployment context.
- The response is read from the startup-loaded runtime bundle and does not recompute explainability values inside the API process.
- Startup loading now accepts the current dict-shaped artifact and also normalizes legacy list-shaped saved payloads defensively if older local bundles are encountered.
- If `global_importance.json` is missing at startup, the endpoint returns a structured `503` with `missing_artifacts`.

### Response

Uses the `GlobalImportanceResponse` shape documented below.

## GET /api/score-distribution

Current foundation note:
- The score-distribution endpoint now serves the saved histogram and summary payload from `models/reports/population_percentiles.json`.
- The response reflects the active runtime model's saved percentile table when the artifact contains multiple model-specific payloads.
- If `population_percentiles.json` is missing at startup, the endpoint returns a structured `503` with `missing_artifacts`.

### Response

```json
{
  "model_name": "logistic_regression",
  "row_count": 10000,
  "summary": {
    "min_score": 300,
    "max_score": 850,
    "mean_score": 590.8,
    "median_score": 596.0
  },
  "score_histogram": [
    {
      "label": "300-349",
      "score_min": 300,
      "score_max": 349,
      "count": 367,
      "share": 0.0367
    }
  ]
}
```

## GET /api/roc-data

Current foundation note:
- The ROC endpoint now serves the saved test-split `roc_curve` payloads from `models/reports/metrics.json`.
- The response is a list of model series and does not run any model inference at request time.
- If `metrics.json` is missing at startup, the endpoint returns a structured `503` with `missing_artifacts`.

### Response

```json
[
  {
    "model_name": "logistic_regression",
    "model_type": "classical",
    "split": "test_months_11_12",
    "points": [
      {
        "fpr": 0.0,
        "tpr": 0.0
      },
      {
        "fpr": 1.0,
        "tpr": 1.0
      }
    ]
  }
]
```

## GET /api/pr-curve

Current foundation note:
- The PR endpoint now serves the saved test-split `pr_curve` payloads from `models/reports/metrics.json`.
- The response is a list of model series and does not run any model inference at request time.
- If `metrics.json` is missing at startup, the endpoint returns a structured `503` with `missing_artifacts`.

### Response

```json
[
  {
    "model_name": "logistic_regression",
    "model_type": "classical",
    "split": "test_months_11_12",
    "points": [
      {
        "recall": 1.0,
        "precision": 0.72
      }
    ]
  }
]
```

## GET /api/calibration-curve

Current foundation note:
- The calibration endpoint now serves the saved test-split `calibration_curve` payloads from `models/reports/metrics.json`.
- The response is a list of model series and does not run any model inference at request time.
- If `metrics.json` is missing at startup, the endpoint returns a structured `503` with `missing_artifacts`.

### Response

```json
[
  {
    "model_name": "logistic_regression",
    "model_type": "classical",
    "split": "test_months_11_12",
    "points": [
      {
        "mean_predicted": 0.45,
        "fraction_positive": 0.52,
        "count": 168
      }
    ]
  }
]
```

## GET /api/confusion-matrix

Current foundation note:
- The confusion-matrix endpoint now serves the saved test-split `confusion_matrix` payloads from `models/reports/metrics.json`.
- The response is a list of per-model matrices at the saved validation-selected threshold and does not run any model inference at request time.
- If `metrics.json` is missing at startup, the endpoint returns a structured `503` with `missing_artifacts`.

### Response

```json
[
  {
    "model_name": "logistic_regression",
    "model_type": "classical",
    "split": "test_months_11_12",
    "threshold": 0.24,
    "tp": 1245,
    "fp": 331,
    "fn": 54,
    "tn": 170,
    "tpr": 0.9584,
    "fpr": 0.6607,
    "fnr": 0.0416
  }
]
```

## Analytics Schemas

### Model Stats Item

```json
{
  "model_name": "stacking_ensemble",
  "model_type": "ensemble",
  "auc_roc": 0.81,
  "auc_pr": 0.86,
  "ks_statistic": 0.47,
  "brier_score": 0.14,
  "expected_calibration_error": 0.03,
  "accuracy": 0.76,
  "precision": 0.79,
  "recall": 0.82,
  "f1": 0.80,
  "threshold": 0.45,
  "split": "test_months_11_12"
}
```

### Baseline Comparison Item

```json
{
  "model_name": "simulated_loan_officer",
  "model_type": "baseline",
  "auc_roc": 0.68,
  "ks_statistic": 0.28,
  "brier_score": 0.19,
  "expected_calibration_error": 0.08,
  "lift_vs_loan_officer": 0.0
}
```

### Score Distribution Response

```json
{
  "model_name": "logistic_regression",
  "row_count": 10000,
  "summary": {
    "min_score": 300,
    "max_score": 850,
    "mean_score": 590.8,
    "median_score": 596.0
  },
  "score_histogram": [
    {
      "label": "300-349",
      "score_min": 300,
      "score_max": 349,
      "count": 367,
      "share": 0.0367
    }
  ]
}
```

### ROC Curve Response

```json
[
  {
    "model_name": "logistic_regression",
    "model_type": "classical",
    "split": "test_months_11_12",
    "points": [
      {
        "fpr": 0.0,
        "tpr": 0.0
      }
    ]
  }
]
```

### Precision-Recall Response

```json
[
  {
    "model_name": "logistic_regression",
    "model_type": "classical",
    "split": "test_months_11_12",
    "points": [
      {
        "recall": 1.0,
        "precision": 0.72
      }
    ]
  }
]
```

### Calibration Curve Response

```json
[
  {
    "model_name": "logistic_regression",
    "model_type": "classical",
    "split": "test_months_11_12",
    "points": [
      {
        "mean_predicted": 0.45,
        "fraction_positive": 0.52,
        "count": 168
      }
    ]
  }
]
```

### Confusion Matrix Response

```json
[
  {
    "model_name": "logistic_regression",
    "model_type": "classical",
    "split": "test_months_11_12",
    "threshold": 0.24,
    "tp": 1245,
    "fp": 331,
    "fn": 54,
    "tn": 170,
    "tpr": 0.9584,
    "fpr": 0.6607,
    "fnr": 0.0416
  }
]
```

### Global Importance Response

```json
{
  "model_name": "xgboost",
  "model_type": "classical",
  "items": [
    {
      "feature": "future_orientation",
      "display_name": "Future Orientation",
      "mean_abs_shap": 0.083,
      "category": "psychometric",
      "rank": 1
    }
  ]
}
```

### Drift Report

```json
{
  "max_psi": 0.12,
  "verdict": "stable",
  "thresholds": {
    "stable_below": 0.2,
    "watch_below": 0.3,
    "alert_at_or_above": 0.3
  },
  "top_drifted_features": [
    {
      "feature": "typing_speed_wpm",
      "psi": 0.12,
      "status": "stable"
    }
  ],
  "all_features": []
}
```

### Fairness Report

```json
{
  "overall_auc": 0.81,
  "overall_approval_rate": 0.64,
  "overall_default_rate": 0.28,
  "worst_auc_gap": 0.03,
  "flagged_groups": [],
  "verdict": "Model shows acceptable fairness across all tested demographic groups.",
  "groups": {
    "gender": {
      "female": {
        "n_samples": 450,
        "auc": 0.80,
        "auc_gap_from_overall": 0.01,
        "approval_rate": 0.63,
        "fpr": 0.14,
        "fnr": 0.18,
        "mean_score": 688.4,
        "flag": "green"
      }
    }
  }
}
```

## API Contract Change Rules

- Adding optional response fields is allowed if frontend defaults are safe.
- Removing or renaming fields requires a new decision entry.
- Changing score mapping semantics requires updates to `DATA_SCHEMA.md`, `MODEL_REGISTRY.md`, and frontend display logic.
- Analytics endpoint files must include enough metadata for dashboard labels and timestamps.
