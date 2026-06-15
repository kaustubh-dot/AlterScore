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
| Calibrated stacking model | `models/artifacts/calibrated_stacking.pkl` | Calibration job | No | Benchmark and rollback/reference artifact |
| Monotonic XGBoost model | `models/artifacts/xgboost_monotonic.pkl` | Governed constrained-tree promotion | Yes | Active manifest runtime |
| SHAP explainer | `models/explainers/shap_explainer_monotonic.pkl` | Explainability job | Yes | Active per-user explanation artifact |
| DICE explainer | `models/explainers/dice_explainer_monotonic.pkl` | Counterfactual job | Yes | Active counterfactual action artifact |
| Metrics report | `models/reports/metrics_monotonic.json` | Evaluation job | Yes for dashboard | Active runtime metrics and curves |
| Baseline metrics | `models/reports/baseline_metrics_monotonic.json` | Baselines job | Yes for dashboard | Active-runtime comparison baselines |
| Global importance | `models/reports/global_importance_monotonic.json` | Explainability job | Yes for dashboard | Dashboard-ready feature ranking for the active monotonic runtime |
| SHAP summary image | `models/reports/shap_summary.png` | SHAP job | No | Human inspection |
| Fairness report | `models/reports/fairness_report_monotonic.json` | Fairness job | Yes for dashboard | Group metrics and verdict across protected audit attributes, plus calibration-parity curves/ECE gaps and the individual-fairness proxy |
| PSI report | `models/reports/psi_report_monotonic.json` | Drift job | Yes for dashboard | Train months `1-8` vs test months `11-12` on the canonical 35 inputs only |
| Population percentiles | `models/reports/population_percentiles_monotonic.json` | Evaluation job | Yes | Score percentile lookup plus saved score histogram for the active runtime |
| Model manifest | `models/registry/production_manifest.json` | Promotion step | Yes | Single serving bundle declaration |
| Promotion gate policy | `models/registry/promotion_gate_policy.json` | Governance policy | Yes for promotion review | Versioned thresholds for AUC, calibration, fairness, governance-impact, and drift gates |

## Production Manifest Schema

Manifest contract notes:

- The manifest now uses exact runtime artifact keys rather than ambiguous aliases, so the loader can validate one coherent bundle contract for startup, health, and analytics.
- Every manifest-declared artifact entry must be an object with deterministic `path` and lowercase SHA256 `sha256` fields.
- The backend validates the manifest structure before startup and verifies each manifest-backed artifact checksum during loading.

```json
{
  "manifest_schema_version": "1.0.0",
  "manifest_version": "xgboost_monotonic_calibrated_v4",
  "model_version": "0.7.0",
  "run_id": "20260615_180711_xgboost_monotonic_calibrated",
  "created_at": "2026-06-15T18:07:13Z",
  "code_ref": "main",
  "data_version": "synthetic_v2.0.0_generated",
  "feature_registry_version": "0.1.0",
  "runtime_model_name": "xgboost_monotonic",
  "runtime_model_type": "classical_monotonic",
  "target": "repayment_label",
  "split": {
    "train": "cohort_month 1-8",
    "validation": "cohort_month 9-10",
    "test": "cohort_month 11-12"
  },
  "artifacts": {
    "runtime_model": {
      "path": "models/artifacts/xgboost_monotonic.pkl",
      "sha256": "..."
    },
    "preprocessor": {
      "path": "models/preprocessors/preprocessor_monotonic.pkl",
      "sha256": "..."
    },
    "text_pca": {
      "path": "models/preprocessors/text_pca.pkl",
      "sha256": "..."
    },
    "shap_explainer": {
      "path": "models/explainers/shap_explainer_monotonic.pkl",
      "sha256": "..."
    },
    "dice_explainer": {
      "path": "models/explainers/dice_explainer_monotonic.pkl",
      "sha256": "..."
    },
    "metrics": {
      "path": "models/reports/metrics_monotonic.json",
      "sha256": "..."
    },
    "baseline_metrics": {
      "path": "models/reports/baseline_metrics_monotonic.json",
      "sha256": "..."
    },
    "fairness_report": {
      "path": "models/reports/fairness_report_monotonic.json",
      "sha256": "..."
    },
    "psi_report": {
      "path": "models/reports/psi_report_monotonic.json",
      "sha256": "..."
    },
    "global_importance": {
      "path": "models/reports/global_importance_monotonic.json",
      "sha256": "..."
    },
    "population_percentiles": {
      "path": "models/reports/population_percentiles_monotonic.json",
      "sha256": "..."
    }
  },
  "metrics_summary": {
    "test_auc_roc": null,
    "test_auc_pr": null,
    "test_ks": null,
    "test_brier": null,
    "test_ece": null
  },
  "fairness_summary": {
    "worst_auc_gap": null,
    "calibration_max_ece_gap": null,
    "individual_fairness_flagged_pair_share": null,
    "flagged_groups": []
  },
  "drift_summary": {
    "max_psi": null,
    "verdict": null
  },
  "score_mapping": {
    "method": "log_odds",
    "score_base": 595.0,
    "log_odds_factor": 64.92,
    "probability_clip_min": 0.000001,
    "probability_clip_max": 0.99,
    "score_min": 300,
    "score_max": 850,
    "calibration": "isotonic"
  },
  "promotion_status": "promoted",
  "promotion_notes": "Calibrated monotonic XGBoost bundle regenerated from the deterministic synthetic v2 generator."
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

- Gate thresholds are versioned in `models/registry/promotion_gate_policy.json`.
- Run `python -m backend.ml.registry.promotion_gates --manifest models/registry/production_manifest.json` before release; use `--require-clean-pass` for promotion-candidate review.
- Runtime AUC on months 11-12 test split is at least 0.75, target above 0.78.
- Ensemble beats simulated loan officer by at least 0.05 AUC.
- Ensemble beats or ties all individual production candidates.
- Brier score and ECE are reported after calibration, and expected calibration error must clear the active policy threshold.
- Score mapping is monotonic from repayment probability to 300-850 score and its parameters are declared in `production_manifest.json`.
- SHAP explanations are non-trivial and produce top factors.
- DICE actions produce 1-3 valid actions and never suggest protected attributes.
- PSI report exists and no core feature has PSI above 0.30 without explanation.
- Fairness report exists, subgroup performance is evaluated, and individual-fairness proxy failures block promotion.
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

The calibrated monotonic `XGBoost` runtime (`xgboost_monotonic` v0.4.0) is the active production runtime.

Current local runtime-artifact status:

- `models/registry/production_manifest.json` freezes the manifest-backed serving bundle for the monotonic `XGBoost` runtime.
- The local manifest-backed bundle declares and checksum-locks the runtime model, monotonic preprocessor, text PCA, monotonic SHAP explainer, monotonic DICE explainer, monotonic metrics, monotonic baseline metrics, monotonic fairness report, monotonic PSI report, monotonic global-importance report, and monotonic population-percentiles artifact set.
- Default local backend startup now prefers the checked-in manifest-backed bundle, while `ALTERSCORE_RUNTIME_MODEL_PATH` remains an explicit override for tests or intentional direct-model runs.
- `models/preprocessors/text_pca.pkl` exists and is loaded by the runtime bundle.
- `models/reports/population_percentiles_monotonic.json` exists and drives the active score distribution response.
- `models/reports/fairness_report_monotonic.json` exists and is generated offline from held-out months `11-12` using protected attributes only for subgroup evaluation. The model shows acceptable fairness across all tested demographic groups (no subgroup AUC deviation >4% from the overall model), includes post-governance impact, and reports individual-fairness proxy flagged-pair share `0.027` with max similar-pair score gap `130`. Similarity is computed over the model's active (non-masked) features only.
- `models/reports/psi_report_monotonic.json` exists and reports a `stable` drift verdict (max PSI `0.0152`).
- `models/reports/global_importance_monotonic.json` exists, is generated offline from the canonical 35 model inputs, and matches the active backend response contract.
- `models/explainers/shap_explainer_monotonic.pkl` is present on disk, deserializes through `backend.ml.explainability.shap_explainer`, passes runtime validation for the checked-in bundle, and drives the checked-in bundle's per-user score explanations.
- `models/explainers/dice_explainer_monotonic.pkl` is present on disk, validates through `backend.ml.explainability.dice_explainer`, and drives the checked-in bundle's persisted counterfactual score actions.
- The curated local runtime bundle is now intentionally source-controlled for portability and smoke coverage, while heavier future training outputs remain ignored by default.
- `/api/score` now emits persisted counterfactual actions from the checked-in artifact, and the code-level default builder remains only a non-default contingency for intentionally artifact-less test bundles.
- Zero-filled semantic fallback remains supported only for intentionally PCA-less test/runtime bundles.
- The current monotonic metrics artifact reports test AUC `0.7787`, Brier score `0.1768`, expected calibration error `0.0346`, and calibration `isotonic`.
- The current monotonic fairness artifact reports `overall_auc = 0.7787` and a fairness verdict of `passed`.
- The current monotonic PSI artifact reports `max_psi = 0.0152` and overall verdict `stable`.
- The current monotonic global-importance artifact ranks features based on mean absolute SHAP values matching the active backend response.

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
- Notes: This baseline run persists the real `text_pca.pkl` from train months `1-8`. The manifest was originally pointed at this logistic runtime candidate during early development, was later promoted to the stacking ensemble, and is now superseded by the monotonic `XGBoost` runtime.

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

### Neural TabNet Smoke Run: `EXP-20260515-008` (offline-only, not promotable)

- Status: neural training infrastructure validated, not promotable standalone
- Date: 2026-05-15
- Branch: `antigravity/dev`
- Dataset: `data/raw/synthetic_dataset.csv` with months `1-8 / 9-10 / 11-12`
- Module: `backend/ml/training/neural/train_tabnet.py`
- CLI: `scripts/training/train_tabnet.py`
- Dependency: `pytorch-tabnet==4.1.0` pinned in `backend/requirements.txt`
- Artifact path: `models/artifacts/tabnet_epoch_best.zip` (not checked in; offline-only until stacking)
- Smoke test suite: `tests/integration/pipeline/test_tabnet_training.py` (6/6 passing)
- AUC target: above `0.72` on test split months `11-12` (see MODEL_REGISTRY.md Model Families table)
- Notes: the TabNet module strictly reuses the existing `align_text_features_from_raw_text`, `prepare_temporal_data`, `fit_preprocessor`, `transform_features`, evaluation metrics, and `merge_evaluation_details`/`merge_population_percentiles_reports` infrastructure. The `.zip` save/load contract is exercised end-to-end in the smoke roundtrip test. Neural metrics merge cleanly into `metrics.json` and `population_percentiles.json` without dropping classical or baseline entries. No manifest or serving path was modified.

### Neural Residual MLP Smoke Run: `EXP-20260515-009` (offline-only, not promotable)

- Status: neural training infrastructure validated, not promotable standalone
- Date: 2026-05-15
- Branch: `antigravity/dev`
- Dataset: `data/raw/synthetic_dataset.csv` with months `1-8 / 9-10 / 11-12`
- Module: `backend/ml/training/neural/train_mlp.py`
- CLI: `scripts/training/train_mlp.py`
- Dependency: `torch>=1.3` (transitively pinned via `pytorch-tabnet==4.1.0`)
- Artifact path: `models/artifacts/mlp_best.pt` (not checked in; offline-only until stacking)
- Artifact format: `torch.save` checkpoint containing `model_name`, `config`, and `state_dict`
- Architecture: `ResidualMLP` — 2-block (Linear→BatchNorm→ReLU→Dropout) with skip projections, Adam optimiser, early stopping on validation AUC, class-imbalance weighting
- Smoke test suite: `tests/integration/pipeline/test_mlp_training.py` (6/6 passing)
- AUC target: above `0.72` on test split months `11-12` (see Model Families table)
- Notes: the MLP module mirrors `train_tabnet.py` exactly in structure and reuses the same preprocessing, temporal-split, evaluation, and metrics infrastructure. The `.pt` save/load round-trip is validated in the smoke roundtrip test: loaded model produces bit-identical probabilities. MLP metrics merge into `metrics.json` and `population_percentiles.json` without dropping TabNet, classical, or baseline entries. No manifest or serving path was modified. Track B (neural) is now complete.

### Calibrated Stacking Ensemble Smoke Run: `EXP-20260515-010` (offline-only, promotion candidate)

- Status: neural training infrastructure validated, not yet promoted to manifest
- Date: 2026-05-15
- Branch: `antigravity/dev`
- Dataset: `data/raw/synthetic_dataset.csv` with months `1-8 / 9-10 / 11-12`
- Module: `backend/ml/training/ensemble/train_stacking.py`
- CLI: `scripts/training/train_stacking.py`
- Base models: logistic_regression, random_forest, xgboost, lightgbm, tabnet, residual_mlp (all 6)
- Meta-learner: `LogisticRegression(C=1.0, solver=lbfgs)` fitted on stacked validation-month probabilities
- Calibration: `CalibratedClassifierCV(FrozenEstimator(meta_learner), method='isotonic')` on validation months 9-10
- Artifact path: `models/artifacts/calibrated_stacking.pkl` (not checked in; offline-only until manifest promotion)
- Config sidecar: `models/artifacts/calibrated_stacking_config.json`
- Smoke test suite: `tests/integration/pipeline/test_stacking_training.py` (6/6 passing)
- AUC target: above best base-model test AUC on months `11-12` (calibration + ensemble should improve over logistic ~0.81)
- Notes: the stacking module accepts `StackingInputs` (pre-computed base model probability arrays) or re-trains all six base models automatically. The meta-learner and isotonic calibrator are fitted on months 9-10 only (no test contamination). The `.pkl` round-trip is validated: loaded model produces bit-identical probabilities. Stacking metrics merge cleanly into `metrics.json` and `population_percentiles.json`. The `default_model_name` in the percentile report is updated to the model with the highest test AUC. Track C (ensemble + calibration) is now complete.

### Calibrated Stacking Promotion Run: `EXP-20260515-011` (promoted → reverted)

- Status: Promotion completed on 2026-05-15, then reverted on 2026-05-16.
- Date: 2026-05-15
- Branch: `antigravity/dev`
- Dataset: `data/raw/synthetic_dataset.csv` with months `1-8 / 9-10 / 11-12`
- Module: `backend/ml/training/ensemble/promote_ensemble.py`
- CLI: `scripts/training/promote_ensemble.py`
- Artifact paths:
  - `models/artifacts/calibrated_stacking.pkl`
  - `models/explainers/shap_explainer.pkl`
  - `models/explainers/dice_explainer.pkl`
  - `models/reports/global_importance.json`
  - `models/reports/fairness_report.json`
  - `models/reports/psi_report.json`
  - `models/registry/production_manifest.json`
- Test AUC: `0.8051`
- Notes: The `calibrated_stacking` ensemble was successfully promoted to `production_manifest.json` as `stacking_ensemble` (v0.2.0). The ensemble inference adapter (`ensemble_adapter.py`) was implemented to transform 35 preprocessed features → 6 base-model probabilities → meta-learner input. DEC-0016 (the revert decision) was superseded by DEC-0017 (ensemble serving restored). The production manifest now points to `calibrated_stacking.pkl` with all 6 base models and the stacking config verified by SHA256 checksums.

### Calibrated Monotonic XGBoost Promotion Run: `20260611_051632_xgboost_monotonic_calibrated`

- Status: active production runtime
- Date: 2026-06-15
- Code reference: `main`
- Training command: `.\.venv312\Scripts\python.exe scripts\training\train_calibrated_monotonic_xgboost.py --device cuda`
- Runtime model: `models/artifacts/xgboost_monotonic.pkl`
- Runtime type: `classical_monotonic`
- Manifest: `models/registry/production_manifest.json`
- Manifest version: `xgboost_monotonic_calibrated_v4`
- Model version: `0.7.0`
- Calibration: isotonic, fit on validation months `9-10`
- Score mapping: FICO-style `log_odds`, `score_base=595`, `log_odds_factor=64.92`, `probability_clip_min=0.000001`, `probability_clip_max=0.99`, `calibration=isotonic` (base/factor derived from PDO=45, anchor 640 @ 2:1 odds)
- Checked-in test AUC: `0.7787`
- Checked-in test Brier score: `0.1768`
- Checked-in test ECE: `0.0346`
- Checked-in PSI verdict: `stable` (Max PSI `0.0152`)
- Checked-in fairness status: `passed` (individual-fairness proxy flagged-pair share `0.027`, max similar-pair score gap `130`)
- Promotion gates: `passed`, with no blocking failures, under `promotion_gate_policy_v2` (includes score-distribution gates).
- Score drivers: creditworthiness is driven by hard-to-fake objective cognition (`numeracy_score` is the #1 SHAP feature) and scenario psychometrics. Spoofable process-timing telemetry (`scroll_hesitation_score`, `session_duration_sec`) is excluded from the causal repayment label in the synthetic generator and feeds only the post-model anti-gaming governance multiplier.
- Notes: `scripts/training/train_calibrated_monotonic_xgboost.py` rebuilds the model, calibration layer, reports, explainers, and manifest from the deterministic synthetic v2 generator. XGBoost training uses CUDA and `n_jobs=-1`; serving saves the calibrated estimator in CPU mode for runtime portability.

### Historical Monotonic XGBoost Promotion Run: `20260527_051352_xgboost_monotonic_promotion`

- Status: superseded by calibrated v0.4.0 runtime
- Date: 2026-05-27
- Historical code reference: `antigravity/dev`
- Runtime model: `models/artifacts/xgboost_monotonic.pkl`
- Runtime type: `classical_monotonic`
- Manifest: `models/registry/production_manifest.json`
- Manifest version: `xgboost_monotonic_v2`
- Checked-in test AUC: `0.7596`
- Checked-in post-governance AUC: `0.7590`
- Checked-in Brier score: *N/A (Monotonic)*
- Checked-in ECE: *N/A (Monotonic)*
- Checked-in PSI verdict: `watch` (Max PSI `0.2052` on `avg_response_time_ms`)
- Checked-in fairness status: `passed` (Model shows acceptable fairness across all tested demographic groups; individual-fairness proxy flagged-pair share `0.2160`)
- Notes: The monotonic XGBoost bundle (v2 assessment) was the default manifest-backed runtime before the calibrated v0.4.0 regeneration. Retrained on v2-calibrated synthetic data: scenario-driven features floored at 0.25, risk_consistency_flag rate tightened to match v2 runtime. Guaranteed monotonicity constraints on all key behavioral features.

