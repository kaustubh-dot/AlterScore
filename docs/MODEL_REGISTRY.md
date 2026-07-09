# AlterScore Model Registry

This document records the current deployable runtime bundle. The machine
readable source of truth is `models/registry/production_manifest.json`.

## Active Runtime

| Field | Value |
|---|---|
| Manifest version | `xgboost_monotonic_calibrated_v4` |
| Model version | `0.7.0` |
| Runtime model | `xgboost_monotonic` |
| Runtime type | `classical_monotonic` |
| Calibration | isotonic |
| Data version | `synthetic_v2.0.0_generated` |
| Promotion status | `promoted` |

The active runtime is a calibrated monotonic `XGBoost` model. It replaced the
earlier ensemble/research candidates because it gives the best deployed balance
of predictive strength, monotonic behavior, calibration, fairness, and runtime
simplicity.

## Required Serving Artifacts

All files below are declared in the production manifest and verified by SHA256
at backend startup.

| Key | Path |
|---|---|
| Runtime model | `models/artifacts/xgboost_monotonic.pkl` |
| Preprocessor | `models/preprocessors/preprocessor_monotonic.pkl` |
| Text PCA | `models/preprocessors/text_pca.pkl` |
| SHAP explainer | `models/explainers/shap_explainer_monotonic.pkl` |
| DICE explainer | `models/explainers/dice_explainer_monotonic.pkl` |
| Metrics | `models/reports/metrics_monotonic.json` |
| Baseline metrics | `models/reports/baseline_metrics_monotonic.json` |
| Fairness report | `models/reports/fairness_report_monotonic.json` |
| PSI report | `models/reports/psi_report_monotonic.json` |
| Global importance | `models/reports/global_importance_monotonic.json` |
| Population percentiles | `models/reports/population_percentiles_monotonic.json` |

## Current Metrics

| Metric | Value |
|---|---:|
| Test AUC ROC | `0.7787` |
| Brier score | `0.1768` |
| Expected calibration error | `0.0346` |
| Max PSI | `0.0152` |
| Individual fairness flagged-pair share | `0.027` |
| Max similar-pair score gap | `130` |

Promotion gates pass under `promotion_gate_policy_v2`, including calibration,
fairness, drift, post-governance impact, and score-distribution gates.

## Registry Rules

- Do not hand-edit serialized model artifacts.
- Do not remove any manifest-declared artifact from the repository or deployment package.
- Do not change `scikit-learn`, XGBoost, or preprocessing dependencies without
  retraining and replacing the bundle.
- Any new production candidate must update the manifest, artifact checksums,
  model reports, and this registry together.
- Promotion requires passing `models/registry/promotion_gate_policy.json`.

## Validation Commands

```bash
python -m backend.ml.registry.promotion_gates --manifest models/registry/production_manifest.json --allow-promoted-incompatibility
python scripts/validation/verify_reproducibility.py
ALTERSCORE_ENV=test python -m pytest tests/integration/api/test_checked_in_runtime_bundle_smoke.py
```

## Reference Artifacts

The repository still contains some non-active classical artifacts and reports
because tests and fallback loaders exercise them. They are not the production
manifest runtime and should not be deleted as part of a docs/noise cleanup.
