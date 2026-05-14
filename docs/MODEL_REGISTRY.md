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
| Text PCA | `models/preprocessors/text_pca.pkl` | NLP/preprocessing job | Yes | Persisted by the current offline baseline/classical jobs and fit on training embeddings only |
| Logistic model | `models/artifacts/logistic_best.pkl` | Classical training | No | Baseline and stack input |
| Random forest model | `models/artifacts/rf_best.pkl` | Classical training | No | SHAP explainability source |
| XGBoost model | `models/artifacts/xgb_best.pkl` | Classical training | No | Stack input |
| LightGBM model | `models/artifacts/lgbm_best.pkl` | Classical training | No | Stack input |
| TabNet model | `models/artifacts/tabnet_epoch_best.zip` | Neural training | No | Stack input |
| MLP model | `models/artifacts/mlp_best.pt` | Neural training | No | Stack input |
| Stacking model | `models/artifacts/stacking_uncalibrated.pkl` | Ensemble training | No | Calibration input |
| Calibrated stacking model | `models/artifacts/calibrated_stacking.pkl` | Calibration job | Yes | Production scoring artifact |
| SHAP explainer | `models/explainers/shap_explainer.pkl` | Explainability job | Yes | Used by score endpoint; the checked-in file now deserializes and validates from repo source, and the current runtime formats per-user SHAP factors from it |
| DICE explainer | `models/explainers/dice_explainer.pkl` | Counterfactual job | Yes | Used by score endpoint; the checked-in file is a validated persisted actionable-counterfactual contract for the current logistic runtime bundle |
| Metrics report | `models/reports/metrics.json` | Evaluation job | Yes for dashboard | All model metrics and curves |
| Baseline metrics | `models/reports/baseline_metrics.json` | Baselines job | Yes for dashboard | Majority, logistic, loan officer, ensemble |
| Global importance | `models/reports/global_importance.json` | Explainability job | Yes for dashboard | Dashboard-ready feature ranking; current foundation prefers exact linear contribution magnitudes from the saved logistic explainability source and keeps the contract field name `mean_abs_shap` for backend compatibility with the existing analytics schema. The checked-in saved payload now matches the active backend response contract. |
| SHAP summary image | `models/reports/shap_summary.png` | SHAP job | No | Human inspection |
| Fairness report | `models/reports/fairness_report.json` | Fairness job | Yes for dashboard | Group metrics and verdict across protected audit attributes; deeper calibration-parity and individual-fairness follow-ons can extend it later |
| PSI report | `models/reports/psi_report.json` | Drift job | Yes for dashboard | Train months `1-8` vs test months `11-12` on the canonical 35 inputs only |
| Population percentiles | `models/reports/population_percentiles.json` | Evaluation job | Yes | Score percentile lookup plus saved score histogram; current payload can hold model-specific tables and a default serving view |
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

Current local runtime-artifact status:

- `models/preprocessors/text_pca.pkl` now exists and is loaded opportunistically by the runtime bundle.
- `models/reports/population_percentiles.json` now exists and the runtime loader resolves the active model's table when the artifact contains multiple model-specific payloads.
- `models/reports/fairness_report.json` now exists and is generated offline from held-out months `11-12` using protected attributes only for subgroup evaluation, never as model inputs.
- `models/reports/psi_report.json` now exists and is generated offline from the canonical 35 model inputs by comparing train months `1-8` to test months `11-12` only.
- `models/reports/global_importance.json` now exists, is generated offline from the canonical 35 model inputs using the current saved explainability source, and the checked-in payload now matches the active backend response contract.
- `models/explainers/shap_explainer.pkl` is now present on disk, deserializes through the restored `backend.ml.explainability.shap_explainer` module, passes runtime validation for the current stub bundle, and drives the checked-in bundle's per-user score explanations.
- `models/explainers/dice_explainer.pkl` is now present on disk, validates through `backend.ml.explainability.dice_explainer`, and drives the checked-in bundle's persisted counterfactual score actions.
- The curated local runtime bundle is now intentionally source-controlled for portability and smoke coverage, while heavier future training outputs remain ignored by default.
- `/api/score` now emits persisted counterfactual actions from the checked-in artifact, and the code-level default builder remains only a non-default contingency for intentionally artifact-less test bundles.
- Zero-filled semantic fallback remains supported only for intentionally PCA-less test/runtime bundles.
- The current local fairness artifact reports `overall_auc = 0.8098`, `worst_auc_gap = 0.0379`, and no flagged groups in the saved subgroup summary.
- The current local PSI artifact reports `max_psi = 0.2007`, overall verdict `watch`, and `avg_response_time_ms` as the most drifted feature.
- The current local global-importance artifact ranks `cognitive_load_index` first at `mean_abs_shap = 0.4635`, followed by `impulsivity_index`, `scroll_hesitation_score`, and `repayment_intention_score`.

### Baseline Run: `20260513_171150_baselines`

- Status: baseline-only candidate, not promotable
- Dataset: `data/raw/synthetic_dataset.csv` with months `1-8 / 9-10 / 11-12`
- Saved artifacts:
  - `models/preprocessors/preprocessor.pkl`
  - `models/preprocessors/text_pca.pkl`
  - `models/artifacts/logistic_best.pkl`
  - `models/reports/baseline_metrics.json`
  - `models/reports/metrics.json`
  - `models/reports/population_percentiles.json`
- Logistic regression validation AUC: `0.8099`
- Logistic regression test AUC: `0.8098`
- Simulated loan officer test AUC: `0.7614`
- Logistic lift vs simulated loan officer: `+0.0484`
- Notes: this refresh persists the real `text_pca.pkl` from train months `1-8` by reconstructing deterministic runtime-compatible surrogate Q27 text from the saved synthetic dataset before PCA fitting, and it also writes the first real `population_percentiles.json` plus validation/test evaluation details into `metrics.json`.

### Classical Run: `20260513_171216_classical`

- Status: classical-model candidate set, not promotable
- Dataset: `data/raw/synthetic_dataset.csv` with months `1-8 / 9-10 / 11-12`
- Saved artifacts:
  - `models/preprocessors/preprocessor.pkl`
  - `models/preprocessors/text_pca.pkl`
  - `models/artifacts/rf_best.pkl`
  - `models/artifacts/xgb_best.pkl`
  - `models/artifacts/lgbm_best.pkl`
  - `models/reports/metrics.json`
  - `models/reports/population_percentiles.json`
- Validation AUCs:
  - Random forest: `0.7945`
  - XGBoost: `0.7993`
  - LightGBM: `0.7959`
- Test AUCs:
  - Random forest: `0.8070`
  - XGBoost: `0.8072`
  - LightGBM: `0.7983`
- Notes: the refreshed classical suite reuses the persisted train-only `text_pca.pkl`, preserves the baseline section in `metrics.json`, adds validation/test ROC, PR, calibration, and confusion payloads for the current logistic/classical models, and merges model-specific score percentile tables into `population_percentiles.json`. The bounded classical suite still trails the logistic baseline test AUC of `0.8098`, so the default percentile table remains `logistic_regression` for now and these remain training-infrastructure milestones rather than promotion candidates.
