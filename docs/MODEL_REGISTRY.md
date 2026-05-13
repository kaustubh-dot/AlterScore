# AlterScore Model Registry

## Purpose

This file tracks expected model artifacts, promotion criteria, and the registry entry template for trained models. It is not a binary artifact registry; it is the human-readable source of truth for what artifacts exist and why they are allowed to serve traffic.

## Registry Principles

- No model is "production" until it has metrics, fairness, drift, calibration, and artifact metadata.
- Production inference must load a complete artifact bundle, not individual ad hoc files.
- A model trained on random split only cannot be promoted.
- A model that uses protected attributes as inputs cannot be promoted.
- Every artifact must be reproducible from a documented data version, code version, config, and seed.

## Expected Artifact Inventory

| Artifact | Path | Producer | Required For Serving | Notes |
|---|---|---|---|---|
| Preprocessor | `models/preprocessors/preprocessor.pkl` | Preprocessing fit job | Yes | Includes scaling, imputation, categorical encoding |
| Text PCA | `models/preprocessors/text_pca.pkl` | NLP/preprocessing job | Yes | Fit on training embeddings only |
| Logistic model | `models/artifacts/logistic_best.pkl` | Classical training | No | Baseline and stack input |
| Random forest model | `models/artifacts/rf_best.pkl` | Classical training | No | SHAP explainability source |
| XGBoost model | `models/artifacts/xgb_best.pkl` | Classical training | No | Stack input |
| LightGBM model | `models/artifacts/lgbm_best.pkl` | Classical training | No | Stack input |
| TabNet model | `models/artifacts/tabnet_epoch_best.zip` | Neural training | No | Stack input |
| MLP model | `models/artifacts/mlp_best.pt` | Neural training | No | Stack input |
| Stacking model | `models/artifacts/stacking_uncalibrated.pkl` | Ensemble training | No | Calibration input |
| Calibrated stacking model | `models/artifacts/calibrated_stacking.pkl` | Calibration job | Yes | Production scoring artifact |
| SHAP explainer | `models/explainers/shap_explainer.pkl` | Explainability job | Yes | Used by score endpoint |
| DICE explainer | `models/explainers/dice_explainer.pkl` | Counterfactual job | Yes | Used by score endpoint |
| Metrics report | `models/reports/metrics.json` | Evaluation job | Yes for dashboard | All model metrics and curves |
| Baseline metrics | `models/reports/baseline_metrics.json` | Baselines job | Yes for dashboard | Majority, logistic, loan officer, ensemble |
| Global importance | `models/reports/global_importance.json` | SHAP job | Yes for dashboard | Top feature importances |
| SHAP summary image | `models/reports/shap_summary.png` | SHAP job | No | Human inspection |
| Fairness report | `models/reports/fairness_report.json` | Fairness job | Yes for dashboard | Group metrics and verdict |
| PSI report | `models/reports/psi_report.json` | Drift job | Yes for dashboard | Train vs future cohort stability |
| Population percentiles | `models/reports/population_percentiles.json` | Evaluation job | Yes | Score percentile lookup |
| Model manifest | `models/registry/production_manifest.json` | Promotion step | Yes | Single serving bundle declaration |

## Production Manifest Schema

```json
{
  "model_version": "0.1.0",
  "run_id": "20260513_120000_initial_stack",
  "created_at": "2026-05-13T00:00:00Z",
  "code_ref": "git-sha-or-branch",
  "data_version": "synthetic_v0.1.0",
  "feature_registry_version": "0.1.0",
  "target": "repayment_label",
  "split": {
    "train": "cohort_month 1-8",
    "validation": "cohort_month 9-10",
    "test": "cohort_month 11-12"
  },
  "artifacts": {
    "model": "models/artifacts/calibrated_stacking.pkl",
    "preprocessor": "models/preprocessors/preprocessor.pkl",
    "text_pca": "models/preprocessors/text_pca.pkl",
    "shap_explainer": "models/explainers/shap_explainer.pkl",
    "dice_explainer": "models/explainers/dice_explainer.pkl",
    "metrics": "models/reports/metrics.json",
    "fairness": "models/reports/fairness_report.json",
    "psi": "models/reports/psi_report.json",
    "percentiles": "models/reports/population_percentiles.json"
  },
  "checksums": {},
  "metrics": {
    "test_auc_roc": null,
    "test_ks": null,
    "test_brier": null,
    "test_ece": null,
    "ensemble_auc_lift_vs_loan_officer": null
  },
  "fairness": {
    "worst_auc_gap": null,
    "flagged_groups": []
  },
  "drift": {
    "max_psi": null,
    "verdict": null
  },
  "promotion_status": "not_promoted",
  "promoted_by": null,
  "promotion_notes": ""
}
```

## Model Families

| Family | Role | Expected Minimum |
|---|---|---|
| Majority baseline | Sanity baseline | AUC about 0.50 |
| Logistic regression | Interpretable baseline and stack member | AUC above 0.68 |
| Simulated loan officer | Human-style comparator | AUC about 0.65-0.72 |
| Random forest | Classical non-linear model and SHAP basis | AUC above 0.73 |
| XGBoost | Gradient boosting candidate | AUC above 0.75 |
| LightGBM | Gradient boosting candidate | AUC above 0.74 |
| TabNet | Attention-based tabular neural model | AUC above 0.72 |
| MLP | Residual neural baseline | AUC above 0.71 |
| Stacking ensemble | Production candidate | AUC above 0.78 target, above 0.75 minimum |

## Promotion Gates

- Stacking ensemble AUC on months 11-12 test split is at least 0.75, target above 0.78.
- Ensemble beats simulated loan officer by at least 0.05 AUC.
- Ensemble beats or ties all individual production candidates.
- Brier score and ECE are reported after calibration.
- Score mapping is monotonic from repayment probability to 300-850 score.
- SHAP explanations are non-trivial and produce top factors.
- DICE actions produce 1-3 valid actions and never suggest protected attributes.
- PSI report exists and no core feature has PSI above 0.30 without explanation.
- Fairness report exists and subgroups with at least 30 samples are evaluated.
- Feature list excludes protected attributes and temporal metadata.
- Artifacts load in a clean backend process.

## Registry Entry Template

```markdown
## Model Version: X.Y.Z

- Status: candidate | production | archived
- Run ID:
- Date:
- Owner:
- Code reference:
- Data version:
- Feature registry version:
- Training command:
- Training environment:
- Random seeds:

### Artifacts

| Artifact | Path | Checksum |
|---|---|---|

### Metrics

| Metric | Validation | Test |
|---|---:|---:|
| AUC ROC | | |
| AUC PR | | |
| KS | | |
| Brier | | |
| ECE | | |
| Accuracy | | |
| Precision | | |
| Recall | | |
| F1 | | |

### Baseline Comparison

| Comparator | AUC | Delta |
|---|---:|---:|
| Majority | | |
| Logistic | | |
| Simulated loan officer | | |

### Fairness

- Worst AUC gap:
- Flagged groups:
- Verdict:

### Drift

- Max PSI:
- Verdict:
- Top drifted features:

### Promotion Decision

- Decision:
- Rationale:
- Known risks:
- Follow-up tasks:
```

## Current Registry

No promoted production model exists yet.

### Baseline Run: `20260513_135512_baselines`

- Status: baseline-only candidate, not promotable
- Dataset: `data/raw/synthetic_dataset.csv` with months `1-8 / 9-10 / 11-12`
- Saved artifacts:
  - `models/preprocessors/preprocessor.pkl`
  - `models/artifacts/logistic_best.pkl`
  - `models/reports/baseline_metrics.json`
  - `models/reports/metrics.json`
- Logistic regression test AUC: `0.8097`
- Simulated loan officer test AUC: `0.7614`
- Logistic lift vs simulated loan officer: `+0.0483`
- Notes: no production ensemble, calibration artifact, text PCA artifact, explainers, fairness report, or PSI report exist yet, so this run is useful only as the first offline benchmark.
