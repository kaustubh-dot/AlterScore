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
- Health may currently be `degraded` even when `model_loaded` is `true` if optional runtime artifacts are still missing but scoring-critical artifacts are present.

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
- The response fields above remain required, but while SHAP and DICE artifacts are not implemented yet the backend scoring stub may return empty `explanation` and `counterfactual_actions` lists rather than omitting those fields.
- Until `models/preprocessors/text_pca.pkl` exists, runtime semantic dimensions may use the documented temporary zero-fill fallback inside the stub service.
- Score requests are now append-logged to the backend runtime log path without storing the raw answers or behavioral payload in the JSONL entry.
- Structured `500` errors now expose only a sanitized error type in the client payload; full failure details remain in server-side logs.

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

### Global Importance Item

```json
{
  "feature": "future_orientation",
  "display_name": "Future Orientation",
  "mean_abs_shap": 0.083,
  "category": "psychometric",
  "rank": 1
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
