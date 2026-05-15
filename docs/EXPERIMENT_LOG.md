# AlterScore Experiment Log

## Purpose

Use this file to record ML experiments and meaningful data pipeline experiments. Do not rely on notebook outputs or chat history as the only memory of an experiment.

## Experiment Naming

Format: `EXP-YYYYMMDD-NNN-short-description`

Example: `EXP-20260513-001-initial-rf-baseline`

## Experiment Template

```markdown
## EXP-YYYYMMDD-NNN - Title

- Status: planned | running | completed | failed | superseded
- Owner:
- Date started:
- Date completed:
- Branch / commit:
- Related decision:
- Related issue / task:

### Hypothesis

What do we expect to learn?

### Dataset

- Data version:
- Row count:
- Train split:
- Validation split:
- Test split:
- Protected attributes available:
- Known schema changes:

### Feature Set

- Feature registry version:
- Numeric feature count:
- Categorical feature count:
- Excluded fields:
- NLP configuration:
- Derived features:

### Model / Pipeline Configuration

```json
{
  "model_family": "",
  "random_seed": 42,
  "preprocessing": {},
  "hyperparameters": {},
  "calibration": {},
  "class_imbalance_strategy": ""
}
```

### Commands

```powershell
# Commands used to reproduce the experiment
```

### Results

| Metric | Train | Validation | Test |
|---|---:|---:|---:|
| AUC ROC | | | |
| AUC PR | | | |
| KS | | | |
| Brier | | | |
| ECE | | | |
| Accuracy | | | |
| Precision | | | |
| Recall | | | |
| F1 | | | |

### Baseline Comparison

| Comparator | Metric | Delta |
|---|---:|---:|
| Majority | | |
| Logistic | | |
| Simulated loan officer | | |

### Fairness Summary

- Worst AUC gap:
- Flagged groups:
- Approval-rate gaps:
- Notes:

### Drift Summary

- Max PSI:
- Top drifted features:
- Verdict:

### Artifacts

| Artifact | Path |
|---|---|

### Interpretation

What changed? Why did it likely change?

### Decision

- Promote:
- Continue:
- Stop:
- Follow-up:
```

## Entries

## EXP-20260513-001 - Synthetic dataset materialization and baseline suite

- Status: completed
- Owner: Codex
- Date started: 2026-05-13
- Date completed: 2026-05-13
- Branch / commit: workspace (uncommitted)
- Related decision: existing temporal-split and baseline comparison decisions
- Related issue / task: dataset materialization command and first baseline training loop

### Hypothesis

If the synthetic dataset is materialized with a validation summary first, then a temporal-split logistic baseline and simulated loan officer comparator can produce the first reproducible offline benchmark set without touching protected or temporal leakage paths.

### Dataset

- Data version: `synthetic_v0.1.0`
- Row count: `10,000`
- Train split: months `1-8` (`6,800` rows)
- Validation split: months `9-10` (`1,400` rows)
- Test split: months `11-12` (`1,800` rows)
- Protected attributes available: gender, age group, region, education level
- Known schema changes: none

### Feature Set

- Feature registry version: `0.1.0`
- Numeric feature count: `33`
- Categorical feature count: `2`
- Excluded fields: protected attributes, `cohort_month`, `application_date`, `repayment_label`
- NLP configuration: pre-generated semantic dimensions already present in the synthetic dataset
- Derived features: included

### Model / Pipeline Configuration

```json
{
  "model_family": "baseline_suite",
  "random_seed": 42,
  "preprocessing": {
    "numeric": "median imputer + standard scaler",
    "categorical": "most-frequent imputer + ordinal encoder"
  },
  "hyperparameters": {
    "logistic_regression": {
      "class_weight": "balanced",
      "max_iter": 1000,
      "solver": "liblinear"
    }
  },
  "calibration": {},
  "class_imbalance_strategy": "class_weight=balanced for logistic only"
}
```

### Commands

```powershell
C:\Users\Kaustubh\anaconda3\python.exe scripts/data/generate_synthetic_dataset.py
C:\Users\Kaustubh\anaconda3\python.exe scripts/training/train_baselines.py
```

### Results

| Metric | Train | Validation | Test |
|---|---:|---:|---:|
| AUC ROC | 0.8190 | 0.8127 | 0.8097 |
| AUC PR | 0.8996 | 0.9092 | 0.9107 |
| KS | 0.4861 | 0.4887 | 0.4948 |
| Brier | 0.1732 | 0.1638 | 0.1662 |
| ECE | 0.1276 | 0.1271 | 0.1218 |
| Accuracy | 0.7724 | 0.8079 | 0.7867 |
| Precision | 0.7795 | 0.8314 | 0.7957 |
| Recall | 0.9298 | 0.9222 | 0.9477 |
| F1 | 0.8481 | 0.8745 | 0.8651 |

### Baseline Comparison

| Comparator | Metric | Delta |
|---|---:|---:|
| Majority | AUC ROC 0.5000 | -0.2614 vs simulated loan officer |
| Logistic | AUC ROC 0.8097 | +0.0483 vs simulated loan officer |
| Simulated loan officer | AUC ROC 0.7614 | 0.0000 |

### Fairness Summary

- Worst AUC gap: not computed
- Flagged groups: not computed
- Approval-rate gaps: not computed
- Notes: fairness is intentionally deferred until additional model/report infrastructure exists

### Drift Summary

- Max PSI: not computed
- Top drifted features: not computed
- Verdict: not computed

### Artifacts

| Artifact | Path |
|---|---|
| Synthetic dataset | `data/raw/synthetic_dataset.csv` |
| Validation summary | `data/validation/validation_summary.json` |
| Preprocessor | `models/preprocessors/preprocessor.pkl` |
| Logistic model | `models/artifacts/logistic_best.pkl` |
| Baseline metrics | `models/reports/baseline_metrics.json` |
| Metrics payload | `models/reports/metrics.json` |

### Interpretation

The synthetic dataset materialized cleanly with no missing values, a `30.38%` default rate, and the documented `6,800 / 1,400 / 1,800` split. The logistic regression baseline clearly outperformed the majority floor and modestly beat the simulated loan officer comparator on the future months `11-12` cohort, which is enough to establish a credible baseline floor for the next classical-model pass.

### Decision

- Promote: no
- Continue: yes
- Stop: no
- Follow-up: train random forest, XGBoost, and LightGBM on the same temporal split foundation, then add artifact loading and backend scoring stubs once the classical artifact set stabilizes.

## EXP-20260513-002 - Bounded classical model suite on the documented temporal split

- Status: completed
- Owner: Codex
- Date started: 2026-05-13
- Date completed: 2026-05-13
- Branch / commit: workspace (uncommitted)
- Related decision: existing temporal-split, 35-feature-registry, and offline-training separation decisions
- Related issue / task: random forest, XGBoost, and LightGBM training foundation

### Hypothesis

If the existing preprocessor and temporal split are reused without widening scope, then a bounded classical suite can save stable artifacts and extend `models/reports/metrics.json` without dropping baseline comparisons.

### Dataset

- Data version: `synthetic_v0.1.0`
- Row count: `10,000`
- Train split: months `1-8` (`6,800` rows)
- Validation split: months `9-10` (`1,400` rows)
- Test split: months `11-12` (`1,800` rows)
- Protected attributes available: gender, age group, region, education level
- Known schema changes: none

### Feature Set

- Feature registry version: `0.1.0`
- Numeric feature count: `33`
- Categorical feature count: `2`
- Excluded fields: protected attributes, `cohort_month`, `application_date`, `repayment_label`
- NLP configuration: pre-generated semantic dimensions already present in the synthetic dataset
- Derived features: included

### Model / Pipeline Configuration

```json
{
  "model_family": "classical_suite",
  "random_seed": 42,
  "preprocessing": {
    "numeric": "median imputer + standard scaler",
    "categorical": "most-frequent imputer + ordinal encoder"
  },
  "hyperparameters": {
    "random_forest": {
      "class_weight": "balanced_subsample",
      "min_samples_leaf": 4,
      "n_estimators": 300
    },
    "xgboost": {
      "learning_rate": 0.05,
      "max_depth": 4,
      "n_estimators": 200,
      "subsample": 1.0,
      "colsample_bytree": 1.0
    },
    "lightgbm": {
      "learning_rate": 0.05,
      "n_estimators": 200,
      "subsample": 1.0,
      "colsample_bytree": 1.0,
      "deterministic": true
    }
  },
  "calibration": {},
  "class_imbalance_strategy": "balanced random-forest bootstrap weighting only"
}
```

### Commands

```powershell
C:\Users\Kaustubh\anaconda3\python.exe -m pytest tests/integration/pipeline/test_classical_training.py tests/integration/pipeline/test_dataset_artifacts_and_baselines.py
C:\Users\Kaustubh\anaconda3\python.exe scripts/training/train_classical_models.py
```

### Results

| Model | Split | AUC ROC | AUC PR | KS | Brier | ECE | Accuracy | Precision | Recall | F1 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Random forest | Validation | 0.7924 | 0.8920 | 0.4708 | 0.1539 | 0.0619 | 0.8014 | 0.8295 | 0.9144 | 0.8699 |
| Random forest | Test | 0.8040 | 0.9061 | 0.4798 | 0.1541 | 0.0512 | 0.7806 | 0.7931 | 0.9415 | 0.8610 |
| XGBoost | Validation | 0.8033 | 0.8991 | 0.4816 | 0.1463 | 0.0379 | 0.8079 | 0.8291 | 0.9262 | 0.8749 |
| XGBoost | Test | 0.8087 | 0.9110 | 0.4852 | 0.1500 | 0.0284 | 0.7872 | 0.8009 | 0.9384 | 0.8642 |
| LightGBM | Validation | 0.7980 | 0.9012 | 0.4732 | 0.1501 | 0.0481 | 0.7943 | 0.8154 | 0.9262 | 0.8673 |
| LightGBM | Test | 0.7977 | 0.9062 | 0.4514 | 0.1557 | 0.0354 | 0.7822 | 0.8001 | 0.9307 | 0.8605 |

### Baseline Comparison

| Comparator | Metric | Delta |
|---|---:|---:|
| Logistic | Test AUC ROC 0.8097 | XGBoost -0.0010 |
| Simulated loan officer | Test AUC ROC 0.7614 | XGBoost +0.0473 |
| Majority | Test AUC ROC 0.5000 | XGBoost +0.3087 |

### Fairness Summary

- Worst AUC gap: not computed
- Flagged groups: not computed
- Approval-rate gaps: not computed
- Notes: fairness is still intentionally deferred until later report infrastructure exists

### Drift Summary

- Max PSI: not computed
- Top drifted features: not computed
- Verdict: not computed

### Artifacts

| Artifact | Path |
|---|---|
| Preprocessor | `models/preprocessors/preprocessor.pkl` |
| Random forest model | `models/artifacts/rf_best.pkl` |
| XGBoost model | `models/artifacts/xgb_best.pkl` |
| LightGBM model | `models/artifacts/lgbm_best.pkl` |
| Metrics payload | `models/reports/metrics.json` |

### Interpretation

The bounded classical suite trains cleanly on the documented temporal split and produces deterministic artifacts plus merged report output without dropping the baseline section. On the current synthetic dataset, however, the new models do not materially outperform the logistic baseline, so the value of this run is the training/reporting foundation rather than a new best candidate.

### Decision

- Promote: no
- Continue: yes
- Stop: no
- Follow-up: add artifact-loading and backend scoring stubs against the stable saved artifacts, then proceed to neural and ensemble work later without reopening the classical training contract.

## EXP-20260513-003 - Persisted text PCA artifact foundation and runtime semantic parity refresh

- Status: completed
- Owner: Codex
- Date started: 2026-05-13
- Date completed: 2026-05-13
- Branch / commit: workspace (uncommitted)
- Related decision: existing temporal-split, 35-feature-registry, and offline-training-separation decisions
- Related issue / task: persisted `text_pca.pkl` foundation for offline training and runtime request assembly

### Hypothesis

If the offline baseline and classical training jobs reconstruct deterministic runtime-compatible raw text embeddings from the saved synthetic dataset, then they can persist a real `models/preprocessors/text_pca.pkl` fit on months `1-8` only without changing the canonical 35 inputs, and the runtime scoring path can consume that artifact without losing the documented zero-fill fallback for intentionally PCA-less bundles.

### Dataset

- Data version: `synthetic_v0.1.0`
- Row count: `10,000`
- Train split: months `1-8` (`6,800` rows)
- Validation split: months `9-10` (`1,400` rows)
- Test split: months `11-12` (`1,800` rows)
- Protected attributes available: gender, age group, region, education level
- Known schema changes: none

### Feature Set

- Feature registry version: `0.1.0`
- Numeric feature count: `33`
- Categorical feature count: `2`
- Excluded fields: protected attributes, `cohort_month`, `application_date`, `repayment_label`
- NLP configuration: deterministic surrogate Q27 text reconstruction from saved NLP columns, runtime-compatible raw embeddings, and train-only PCA persistence
- Derived features: included

### Model / Pipeline Configuration

```json
{
  "model_family": "text_pca_artifact_foundation",
  "random_seed": 42,
  "preprocessing": {
    "numeric": "median imputer + standard scaler",
    "categorical": "most-frequent imputer + ordinal encoder",
    "text_pca": "2 components fit on months 1-8 only and saved to models/preprocessors/text_pca.pkl"
  },
  "hyperparameters": {
    "logistic_regression": {
      "class_weight": "balanced",
      "max_iter": 1000,
      "solver": "liblinear"
    },
    "random_forest": {
      "class_weight": "balanced_subsample",
      "min_samples_leaf": 4,
      "n_estimators": 300
    },
    "xgboost": {
      "learning_rate": 0.05,
      "max_depth": 4,
      "n_estimators": 200,
      "subsample": 1.0,
      "colsample_bytree": 1.0
    },
    "lightgbm": {
      "learning_rate": 0.05,
      "n_estimators": 200,
      "subsample": 1.0,
      "colsample_bytree": 1.0,
      "deterministic": true
    }
  },
  "calibration": {},
  "class_imbalance_strategy": "logistic balanced class weights plus bounded classical defaults"
}
```

### Commands

```powershell
C:\Users\Kaustubh\anaconda3\python.exe -m pytest --basetemp .tmp\pytest tests/integration/pipeline/test_preprocessing_split_integrity.py tests/integration/pipeline/test_feature_assembly.py tests/integration/pipeline/test_dataset_artifacts_and_baselines.py tests/integration/pipeline/test_classical_training.py tests/integration/pipeline/test_artifact_loading.py tests/integration/pipeline/test_text_pca_artifact.py tests/integration/api/test_health_endpoint.py tests/integration/api/test_score_endpoint.py
C:\Users\Kaustubh\anaconda3\python.exe scripts/training/train_baselines.py
C:\Users\Kaustubh\anaconda3\python.exe scripts/training/train_classical_models.py
```

### Results

| Metric | Train | Validation | Test |
|---|---:|---:|---:|
| Logistic AUC ROC | 0.8189 | 0.8128 | 0.8104 |
| Logistic AUC PR | 0.8998 | 0.9096 | 0.9111 |
| Logistic KS | 0.4849 | 0.4851 | 0.4894 |
| Logistic Brier | 0.1734 | 0.1637 | 0.1660 |
| Logistic ECE | 0.1276 | 0.1271 | 0.1219 |
| Logistic Accuracy | 0.7712 | 0.8107 | 0.7878 |
| Logistic Precision | 0.7753 | 0.8474 | 0.7949 |
| Logistic Recall | 0.9365 | 0.9016 | 0.9515 |
| Logistic F1 | 0.8483 | 0.8736 | 0.8662 |

### Baseline Comparison

| Comparator | Metric | Delta |
|---|---:|---:|
| Majority | AUC ROC 0.5000 | -0.2614 vs simulated loan officer |
| Logistic | AUC ROC 0.8104 | +0.0490 vs simulated loan officer |
| Simulated loan officer | AUC ROC 0.7614 | 0.0000 |

### Classical Snapshot

| Model | Validation AUC ROC | Test AUC ROC |
|---|---:|---:|
| Random forest | 0.7950 | 0.8055 |
| XGBoost | 0.8022 | 0.8080 |
| LightGBM | 0.7932 | 0.7964 |

### Fairness Summary

- Worst AUC gap: not computed
- Flagged groups: not computed
- Approval-rate gaps: not computed
- Notes: fairness is still intentionally deferred until later report infrastructure exists

### Drift Summary

- Max PSI: not computed
- Top drifted features: not computed
- Verdict: not computed

### Artifacts

| Artifact | Path |
|---|---|
| Text PCA | `models/preprocessors/text_pca.pkl` |
| Preprocessor | `models/preprocessors/preprocessor.pkl` |
| Logistic model | `models/artifacts/logistic_best.pkl` |
| Random forest model | `models/artifacts/rf_best.pkl` |
| XGBoost model | `models/artifacts/xgb_best.pkl` |
| LightGBM model | `models/artifacts/lgbm_best.pkl` |
| Baseline metrics | `models/reports/baseline_metrics.json` |
| Metrics payload | `models/reports/metrics.json` |

### Interpretation

The offline pipeline now persists a real `text_pca.pkl` fit only on months `1-8` and the runtime request-assembly path consumes it whenever it is available. The focused pipeline and API integration suite confirmed that validation/test rows transform cleanly, semantic outputs stay finite, runtime projections become non-zero with the saved artifact, and the zero-fill behavior remains available only when the PCA artifact is intentionally omitted.

### Decision

- Promote: no
- Continue: yes
- Stop: no
- Follow-up: build the analytics report-reading service plus `/api/model-stats` and `/api/baseline-comparison` route stubs on top of the refreshed local artifact bundle.

## EXP-20260513-004 - Offline evaluation artifact foundation for analytics routes

- Status: completed
- Owner: Codex
- Date started: 2026-05-13
- Date completed: 2026-05-13
- Branch / commit: workspace (uncommitted)
- Related decision: existing temporal-split, offline-training-separation, and artifact-loading decisions
- Related issue / task: persisted evaluation bundle for score-distribution and curve/confusion analytics

### Hypothesis

If the offline baseline and classical jobs save score-distribution, percentile, and curve/confusion payloads directly from the documented temporal split plus full scored synthetic population, then the remaining analytics routes can stay read-only at request time and the runtime scoring path can keep using a saved percentile lookup without hidden recomputation.

### Dataset

- Data version: `synthetic_v0.1.0`
- Row count: `10,000`
- Train split: months `1-8` (`6,800` rows)
- Validation split: months `9-10` (`1,400` rows)
- Test split: months `11-12` (`1,800` rows)
- Protected attributes available: gender, age group, region, education level
- Known schema changes: none

### Feature Set

- Feature registry version: `0.1.0`
- Numeric feature count: `33`
- Categorical feature count: `2`
- Excluded fields: protected attributes, `cohort_month`, `application_date`, `repayment_label`
- NLP configuration: persisted-dataset training now rebuilds deterministic surrogate Q27 text when the saved CSV does not include raw text
- Derived features: included

### Model / Pipeline Configuration

```json
{
  "model_family": "evaluation_artifact_foundation",
  "random_seed": 42,
  "preprocessing": {
    "numeric": "median imputer + standard scaler",
    "categorical": "most-frequent imputer + ordinal encoder",
    "text_pca": "2 components fit on months 1-8 only and reused for all scored report payloads"
  },
  "hyperparameters": {
    "logistic_regression": {
      "class_weight": "balanced",
      "max_iter": 1000,
      "solver": "liblinear"
    },
    "random_forest": {
      "class_weight": "balanced_subsample",
      "min_samples_leaf": 4,
      "n_estimators": 300
    },
    "xgboost": {
      "learning_rate": 0.05,
      "max_depth": 4,
      "n_estimators": 200,
      "subsample": 1.0,
      "colsample_bytree": 1.0
    },
    "lightgbm": {
      "learning_rate": 0.05,
      "n_estimators": 200,
      "subsample": 1.0,
      "colsample_bytree": 1.0,
      "deterministic": true
    }
  },
  "calibration": {},
  "class_imbalance_strategy": "unchanged from the bounded baseline/classical suite"
}
```

### Commands

```powershell
C:\Users\Kaustubh\anaconda3\python.exe -m pytest --basetemp .tmp\pytest tests/unit/ml/test_score_mapper.py tests/integration/pipeline/test_dataset_artifacts_and_baselines.py tests/integration/pipeline/test_classical_training.py tests/integration/pipeline/test_artifact_loading.py tests/integration/pipeline/test_evaluation_artifacts.py tests/integration/api/test_health_endpoint.py tests/integration/api/test_score_endpoint.py tests/integration/api/test_analytics_endpoints.py
C:\Users\Kaustubh\anaconda3\python.exe scripts/training/train_baselines.py
C:\Users\Kaustubh\anaconda3\python.exe scripts/training/train_classical_models.py
```

### Results

| Model | Validation AUC ROC | Test AUC ROC |
|---|---:|---:|
| Logistic regression | 0.8099 | 0.8098 |
| Random forest | 0.7945 | 0.8070 |
| XGBoost | 0.7993 | 0.8072 |
| LightGBM | 0.7959 | 0.7983 |

### Baseline Comparison

| Comparator | Metric | Delta |
|---|---:|---:|
| Majority | AUC ROC 0.5000 | -0.2614 vs simulated loan officer |
| Logistic | AUC ROC 0.8098 | +0.0484 vs simulated loan officer |
| Simulated loan officer | AUC ROC 0.7614 | 0.0000 |

### Fairness Summary

- Worst AUC gap: not computed
- Flagged groups: not computed
- Approval-rate gaps: not computed
- Notes: fairness remains intentionally deferred until the dedicated offline fairness job exists

### Drift Summary

- Max PSI: not computed
- Top drifted features: not computed
- Verdict: not computed

### Artifacts

| Artifact | Path |
|---|---|
| Metrics payload with `evaluation_details` | `models/reports/metrics.json` |
| Population percentiles and score histogram | `models/reports/population_percentiles.json` |
| Baseline metrics | `models/reports/baseline_metrics.json` |
| Preprocessor | `models/preprocessors/preprocessor.pkl` |
| Text PCA | `models/preprocessors/text_pca.pkl` |

### Interpretation

The offline pipeline now saves the report foundation needed for `/api/score-distribution`, `/api/roc-data`, `/api/pr-curve`, `/api/calibration-curve`, and `/api/confusion-matrix` without scoring rows inside the API process. The persisted synthetic CSV path now works end-to-end even when raw Q27 text is absent, because preprocessing reconstructs deterministic surrogate text before rebuilding NLP features and embeddings. The runtime bundle also stays model-agnostic by selecting the active model's table from a multi-model `population_percentiles.json` payload.

### Decision

- Promote: no
- Continue: yes
- Stop: no
- Follow-up: wire the remaining analytics routes to the saved evaluation artifacts, starting with `/api/score-distribution` or the grouped curve endpoints.

## EXP-20260513-005 - Persisted PSI drift artifact foundation

- Status: completed
- Owner: Codex
- Date started: 2026-05-13
- Date completed: 2026-05-13
- Branch / commit: workspace (uncommitted)
- Related decision: existing temporal-split, 35-feature-registry, and offline-training-separation decisions
- Related issue / task: persisted `psi_report.json` foundation for the offline governance bundle

### Hypothesis

If the offline drift job reuses the same temporal split and feature-preparation foundations as training, then it can persist a deterministic PSI artifact for the canonical 35 model inputs only, while excluding protected attributes, temporal metadata, and the target from the saved report.

### Dataset

- Data version: `synthetic_v0.1.0`
- Row count: `10,000`
- Train split: months `1-8` (`6,800` rows)
- Validation split: months `9-10` (`1,400` rows, not used for PSI)
- Test split: months `11-12` (`1,800` rows)
- Protected attributes available: gender, age group, region, education level
- Known schema changes: none

### Feature Set

- Feature registry version: `0.1.0`
- Numeric feature count: `33`
- Categorical feature count: `2`
- Included fields: canonical 35 model inputs only
- Excluded fields: protected attributes, `cohort_month`, `application_date`, `repayment_label`
- NLP configuration: drift generation reuses the persisted-dataset text-alignment and train-only PCA preparation foundations before comparing train vs test feature distributions

### Model / Pipeline Configuration

```json
{
  "job_type": "psi_drift_report",
  "random_seed": 42,
  "comparison": {
    "expected_split": "train_months_1_8",
    "actual_split": "test_months_11_12"
  },
  "binning": {
    "numeric": "deterministic train-derived quantile bins",
    "categorical": "deterministic sorted category buckets",
    "bin_count": 10,
    "epsilon": 1e-06
  },
  "thresholds": {
    "stable_below": 0.2,
    "watch_below": 0.3,
    "alert_at_or_above": 0.3
  }
}
```

### Commands

```powershell
C:\Users\Kaustubh\anaconda3\python.exe -m pytest --basetemp .tmp\pytest tests/integration/pipeline/test_dataset_artifacts_and_baselines.py tests/integration/pipeline/test_classical_training.py tests/integration/pipeline/test_artifact_loading.py tests/integration/pipeline/test_psi_report_artifact.py
C:\Users\Kaustubh\anaconda3\python.exe -c "from backend.ml.evaluation.drift import generate_psi_report; artifacts = generate_psi_report(); print(artifacts.report_path); print(artifacts.max_psi); print(artifacts.verdict)"
```

### Drift Summary

- Max PSI: `0.2007`
- Top drifted features: `avg_response_time_ms`, `session_duration_sec`, `cognitive_load_index`, `typing_speed_wpm`
- Verdict: `watch`

### Artifacts

| Artifact | Path |
|---|---|
| PSI drift report | `models/reports/psi_report.json` |

### Interpretation

The offline governance bundle now includes a real persisted drift report without widening scope into fairness, SHAP, DICE, calibration, stacking, or runtime analytics routes. The saved report stays model-agnostic, uses the documented train/test temporal comparison only, and confirms the expected mild synthetic drift is concentrated in later-cohort timing features rather than protected or excluded fields.

### Decision

- Promote: no
- Continue: yes
- Stop: no
- Follow-up: generate the fairness and global-importance artifacts next, then wire `/api/drift-report` together with the remaining governance analytics routes in a later backend slice.

## EXP-20260513-006 - Persisted fairness report artifact foundation

- Status: completed
- Owner: Codex
- Date started: 2026-05-13
- Date completed: 2026-05-13
- Branch / commit: workspace (uncommitted after `ce2152a`)
- Related decision: existing temporal-split, protected-attribute-separation, and offline-training-separation decisions
- Related issue / task: persisted `fairness_report.json` foundation for the offline governance bundle

### Hypothesis

If the offline fairness job reuses held-out test predictions plus the protected audit columns already preserved outside model inputs, then it can persist a backend-schema-compatible fairness report without touching runtime inference, while still enforcing subgroup sample guards and excluding protected fields from the model feature set itself.

### Dataset

- Data version: `synthetic_v0.1.0`
- Row count: `10,000`
- Train split: months `1-8` (`6,800` rows)
- Validation split: months `9-10` (`1,400` rows)
- Test split: months `11-12` (`1,800` rows)
- Protected attributes available: gender, age group, region, education level
- Known schema changes: none

### Feature Set

- Feature registry version: `0.1.0`
- Numeric feature count: `33`
- Categorical feature count: `2`
- Included model inputs: canonical 35 features only
- Protected attributes: retained only in `protected_test` for subgroup evaluation
- Excluded fields from model inputs: protected attributes, `cohort_month`, `application_date`, `repayment_label`
- NLP configuration: persisted-dataset training still rebuilds runtime-compatible text features before scoring when raw Q27 text is absent

### Model / Pipeline Configuration

```json
{
  "job_type": "fairness_report",
  "random_seed": 42,
  "selection": {
    "baseline_run": "logistic_regression only",
    "classical_run": "best available test-AUC model among logistic/classical candidates"
  },
  "approval_rule": {
    "score_threshold": 550,
    "interpretation": "fair-or-better runtime score band"
  },
  "group_guardrails": {
    "minimum_group_samples": 30,
    "yellow_auc_gap_above": 0.04,
    "red_auc_gap_above": 0.07
  },
  "reported_metrics": [
    "overall_auc",
    "overall_approval_rate",
    "overall_default_rate",
    "worst_auc_gap",
    "flagged_groups",
    "per-group auc",
    "approval_rate",
    "fpr",
    "fnr",
    "mean_score",
    "flag"
  ]
}
```

### Commands

```powershell
C:\Users\Kaustubh\anaconda3\python.exe -m pytest --basetemp .tmp\pytest tests/integration/pipeline/test_dataset_artifacts_and_baselines.py tests/integration/pipeline/test_classical_training.py tests/integration/pipeline/test_artifact_loading.py tests/integration/pipeline/test_psi_report_artifact.py tests/integration/pipeline/test_fairness_report_artifact.py
C:\Users\Kaustubh\anaconda3\python.exe -c "from backend.ml.training.classical.baselines import train_baselines; artifacts = train_baselines(); print(artifacts.fairness_report_path)"
```

### Fairness Summary

- Worst AUC gap: `0.0379`
- Flagged groups: none
- Approval-rate gaps: subgroup approval rates vary, but no subgroup exceeds the current saved AUC-gap warning threshold
- Notes: this foundation persists the subgroup fairness summary already supported by the backend schema; calibration-parity curves and the individual-fairness proxy remain deferred follow-on work

### Artifacts

| Artifact | Path |
|---|---|
| Fairness report | `models/reports/fairness_report.json` |

### Interpretation

The offline governance bundle now includes a real fairness report alongside the existing PSI artifact, and it does so without mixing protected attributes into the model inputs or pulling fairness logic into FastAPI request handling. The saved local report currently shows no flagged groups under the bounded AUC-gap policy, which is credible for the synthetic dataset and enough to unblock the later report-backed fairness route.

### Decision

- Promote: no
- Continue: yes
- Stop: no
- Follow-up: generate the global-importance artifact next, then wire `/api/fairness-report`, `/api/drift-report`, and `/api/global-importance` together in the governance analytics route slice.

## EXP-20260514-007 - Persisted global-importance artifact foundation

- Status: completed
- Owner: Codex
- Date started: 2026-05-14
- Date completed: 2026-05-14
- Branch / commit: workspace (uncommitted)
- Related decision: existing temporal-split, 35-feature-registry, and offline-training-separation decisions
- Related issue / task: persisted `global_importance.json` foundation for the offline governance bundle

### Hypothesis

If the offline training bundle reuses the saved explainability-capable models and processed temporal splits, then it can persist a deterministic dashboard-ready `global_importance.json` payload for the canonical 35 inputs without adding runtime routes or requiring a full `shap_explainer.pkl` job yet.

### Dataset

- Data version: `synthetic_v0.1.0`
- Row count: `10,000`
- Train split: months `1-8` (`6,800` rows)
- Validation split: months `9-10` (`1,400` rows)
- Test split: months `11-12` (`1,800` rows)
- Protected attributes available: gender, age group, region, education level
- Known schema changes: none

### Feature Set

- Feature registry version: `0.1.0`
- Numeric feature count: `33`
- Categorical feature count: `2`
- Included fields: canonical 35 model inputs only
- Excluded fields: protected attributes, `cohort_month`, `application_date`, `repayment_label`
- Explainability path: prefer exact linear contribution magnitudes from the saved logistic baseline when available; otherwise fall back to deterministic model-native importances from the current classical bundle

### Model / Pipeline Configuration

```json
{
  "job_type": "global_importance_report",
  "random_seed": 42,
  "selection": {
    "exact_linear_preference": ["logistic_regression"],
    "native_importance_fallback": ["xgboost", "lightgbm", "random_forest"]
  },
  "reference_distribution": {
    "background_split": "train_months_1_8",
    "explained_split": "test_months_11_12"
  },
  "payload": {
    "schema": "GlobalImportanceResponse root list",
    "sort": "descending by mean_abs_shap then feature name",
    "categories": ["psychometric", "behavioral", "nlp", "derived"]
  }
}
```

### Commands

```powershell
C:\Users\Kaustubh\anaconda3\python.exe -m pytest --basetemp .tmp\pytest tests/integration/pipeline/test_dataset_artifacts_and_baselines.py tests/integration/pipeline/test_classical_training.py tests/integration/pipeline/test_artifact_loading.py tests/integration/pipeline/test_psi_report_artifact.py tests/integration/pipeline/test_fairness_report_artifact.py tests/integration/pipeline/test_global_importance_artifact.py
C:\Users\Kaustubh\anaconda3\python.exe scripts/training/train_baselines.py
C:\Users\Kaustubh\anaconda3\python.exe scripts/training/train_classical_models.py
```

### Results

| Artifact Metric | Value |
|---|---:|
| Saved feature count | `35` |
| Top feature | `cognitive_load_index` |
| Top `mean_abs_shap` | `0.4635` |
| Second feature | `impulsivity_index` |
| Third feature | `scroll_hesitation_score` |

### Fairness Summary

- Worst AUC gap: `0.0379`
- Flagged groups: none
- Approval-rate gaps: unchanged from the current saved fairness artifact
- Notes: fairness computation is unchanged in this run; the artifact remained compatible beside the new global-importance report

### Drift Summary

- Max PSI: `0.2007`
- Top drifted features: `avg_response_time_ms`, `session_duration_sec`, `cognitive_load_index`, `typing_speed_wpm`
- Verdict: `watch`

### Artifacts

| Artifact | Path |
|---|---|
| Global importance report | `models/reports/global_importance.json` |

### Interpretation

The offline governance bundle now includes a real dashboard-ready global-importance report without widening scope into runtime analytics routes or the persisted SHAP explainer path. The current saved report is dominated by derived and behavioral features on the held-out test split, which is directionally consistent with the existing logistic baseline and the synthetic dataset's constructed repayment signal.

### Decision

- Promote: no
- Continue: yes
- Stop: no
- Follow-up: wire `/api/fairness-report`, `/api/drift-report`, and `/api/global-importance` to the saved report files, then return to the persisted SHAP explainer and per-user explanation path.

## EXP-20260514-008 - Fairness governance detail refresh for manifest-backed bundle

- Status: completed
- Owner: Codex
- Date started: 2026-05-14
- Date completed: 2026-05-14
- Branch / commit: workspace (pending commit)
- Related decision: existing protected-attribute audit-only and offline-governance decisions
- Related issue / task: calibration parity and individual-fairness proxy for the persisted fairness artifact

### Hypothesis

If calibration parity and the individual-fairness proxy are computed inside the offline fairness report generator, then the checked-in manifest-backed bundle can expose the full PRD governance surface without moving protected attributes or fairness computation into FastAPI request handling.

### Dataset

- Data version: `synthetic_v0.1.0`
- Row count: `10,000`
- Train split: months `1-8`
- Validation split: months `9-10`
- Test split: months `11-12` (`1,800` rows)
- Protected attributes available: gender, age group, region, education level
- Known schema changes: `/api/fairness-report` now includes optional `calibration_parity` and `individual_fairness_proxy` sections

### Feature Set

- Feature registry version: `0.1.0`
- Numeric feature count: `33`
- Categorical feature count: `2`
- Excluded fields: protected attributes, `cohort_month`, `application_date`, `repayment_label`
- Similarity proxy features: the 14 psychometric model-input features only; protected attributes are used only to require demographic difference after similarity is computed

### Commands

```powershell
C:\Users\Kaustubh\anaconda3\python.exe -m pytest tests/unit/ml/test_fairness.py tests/unit/backend/test_analytics_schema.py tests/integration/pipeline/test_fairness_report_artifact.py tests/integration/api/test_analytics_endpoints.py tests/integration/api/test_checked_in_runtime_bundle_smoke.py
C:\Users\Kaustubh\anaconda3\python.exe -m pytest tests/integration/pipeline/test_artifact_loading.py tests/integration/api/test_checked_in_runtime_bundle_smoke.py
```

### Fairness Summary

- Overall AUC: `0.8098`
- Worst subgroup AUC gap: `0.0379`
- Calibration max ECE gap: `0.0528`
- Flagged subgroups: none
- Individual-fairness proxy: `512839` evaluated similar demographic-difference pairs; `374894` exceed the `50` point score-gap threshold

### Artifacts

| Artifact | Path |
|---|---|
| Refreshed fairness report | `models/reports/fairness_report.json` |
| Updated manifest checksum | `models/registry/production_manifest.json` |

### Interpretation

The governance artifact now covers demographic parity, equalized odds, calibration parity, and the PRD individual-fairness proxy while keeping protected attributes outside model inputs. The high pair-flag share is a useful signal for the current synthetic/logistic bundle: psychometrically similar applicants can still diverge sharply because behavioral and derived features drive score movement, so this should be revisited after the calibrated ensemble exists.

### Decision

- Promote: no
- Continue: yes
- Stop: no
- Follow-up: move to the offline neural-model track, then revisit fairness once a calibrated ensemble candidate is available.

## EXP-20260515-008 - TabNet neural training infrastructure (Phase 1)

- Status: completed
- Owner: Antigravity / Codex
- Date started: 2026-05-15
- Date completed: 2026-05-15
- Branch / commit: `antigravity/dev`
- Related decision: neural model track (Track B), offline-training-separation, temporal-split integrity
- Related issue / task: TabNet Phase 1 — offline training module, CLI script, integration smoke tests

### Hypothesis

If the TabNet training module strictly reuses the existing preprocessing, temporal-split, evaluation, and metrics infrastructure (without duplicating any feature paths), then it can produce deterministic `.zip` artifacts, pass a full pipeline smoke-test suite, and merge its output metrics cleanly into the existing `metrics.json` and `population_percentiles.json` without breaking any classical or baseline report consumers.

### Dataset

- Data version: `synthetic_v0.1.0`
- Row count: `10,000` (full run); `1,800` (smoke test)
- Train split: months `1-8`
- Validation split: months `9-10`
- Test split: months `11-12`
- Protected attributes available: gender, age group, region, education level
- Known schema changes: none

### Feature Set

- Feature registry version: `0.1.0`
- Numeric feature count: `33`
- Categorical feature count: `2`
- Excluded fields: protected attributes, `cohort_month`, `application_date`, `repayment_label`
- NLP configuration: same surrogate-text + text-PCA path as classical training
- Derived features: included

### Model / Pipeline Configuration

```json
{
  "model_family": "tabnet_neural",
  "random_seed": 42,
  "dependency": "pytorch-tabnet==4.1.0",
  "preprocessing": {
    "numeric": "median imputer + standard scaler (reused from classical)",
    "categorical": "most-frequent imputer + ordinal encoder (reused from classical)",
    "text_pca": "2 components fit on months 1-8 only (reused artifact)"
  },
  "hyperparameters": {
    "n_d": 16,
    "n_a": 16,
    "n_steps": 3,
    "gamma": 1.3,
    "n_independent": 2,
    "n_shared": 2,
    "momentum": 0.02,
    "epsilon": 1e-15,
    "mask_type": "sparsemax",
    "max_epochs": 50,
    "patience": 10,
    "batch_size": 1024,
    "virtual_batch_size": 256
  },
  "artifact_format": ".zip (pytorch-tabnet native save_model / load_model)",
  "class_imbalance_strategy": "none (TabNet handles internally via eval AUC selection)"
}
```

### Commands

```powershell
# Install dependency
C:\Users\Kaustubh\anaconda3\python.exe -m pip install pytorch-tabnet==4.1.0

# Run smoke tests (all 6 pass in ~23s)
C:\Users\Kaustubh\anaconda3\python.exe -m pytest tests/integration/pipeline/test_tabnet_training.py -v

# Full pipeline regression (81/81 passing)
C:\Users\Kaustubh\anaconda3\python.exe -m pytest tests/integration/pipeline/ tests/unit/ml/ -q

# Train on the full dataset (requires synthetic_dataset.csv and baseline metrics)
C:\Users\Kaustubh\anaconda3\python.exe scripts/training/train_tabnet.py
```

### Results

Smoke tests only (2 epochs, 1,800-row dataset, no saved artifact target AUC recorded).
Full-dataset AUC targets from `docs/MODEL_REGISTRY.md`: above `0.72` on test split months `11-12`.

### Artifacts

| Artifact | Path |
|---|---|
| TabNet training module | `backend/ml/training/neural/train_tabnet.py` |
| Neural package init | `backend/ml/training/neural/__init__.py` |
| CLI entrypoint | `scripts/training/train_tabnet.py` |
| Integration smoke tests (6 tests) | `tests/integration/pipeline/test_tabnet_training.py` |
| Dependency pin | `backend/requirements.txt` (pytorch-tabnet==4.1.0) |
| Artifact (offline, not checked in) | `models/artifacts/tabnet_epoch_best.zip` |

### Interpretation

The TabNet training infrastructure integrates cleanly into the existing pipeline without any duplication of preprocessing or feature paths. The `.zip` save/load round-trip is validated in the smoke test: the loaded model produces bit-identical probabilities to the training-time model. Neural metrics merge into `metrics.json` and `population_percentiles.json` without dropping classical (random_forest, xgboost, lightgbm) or baseline (logistic_regression) rows. The serving/manifest path is untouched. The only downstream dependency change is `pytorch-tabnet==4.1.0` (which pulls PyTorch 2.12.0 as a transitive dependency).

### Decision

- Promote: no
- Continue: yes
- Stop: no
- Follow-up: ~~implement the offline residual MLP training module~~ — done. Proceed to stacking (Track C).

## EXP-20260515-009 - Residual MLP neural training infrastructure (Phase 1)

- Status: completed
- Owner: Antigravity / Codex
- Date started: 2026-05-15
- Date completed: 2026-05-15
- Branch / commit: `antigravity/dev`
- Related decision: neural model track (Track B), offline-training-separation, temporal-split integrity
- Related issue / task: Residual MLP Phase 1 — offline training module, CLI script, 6 integration smoke tests

### Hypothesis

If the residual MLP training module mirrors `train_tabnet.py` (same preprocessing chain, metrics merge, artifact-save pattern) and adds a 2-block residual MLP with early stopping on validation AUC, then it can pass the full 6-test smoke suite and merge its metrics into `metrics.json` without breaking any prior row.

### Dataset

- Data version: `synthetic_v0.1.0`
- Row count: `10,000` (full run); `1,800` (smoke test)
- Train split: months `1-8`; Validation: months `9-10`; Test: months `11-12`
- Protected attributes available: gender, age group, region, education level

### Feature Set

- Feature registry version: `0.1.0`; Numeric: `33`; Categorical: `2`
- Excluded: protected attributes, `cohort_month`, `application_date`, `repayment_label`
- NLP: same surrogate-text + text-PCA path as classical and TabNet

### Model / Pipeline Configuration

```json
{
  "model_family": "residual_mlp",
  "random_seed": 42,
  "architecture": { "hidden_dim": 128, "n_hidden_layers": 2, "dropout": 0.3, "skip_connection": true, "batch_norm": true },
  "training": { "optimiser": "Adam", "lr": 0.001, "weight_decay": 1e-4, "max_epochs": 50, "patience": 10, "batch_size": 512, "class_imbalance": "pos_weight=neg/pos ratio", "early_stopping": "validation_auc" },
  "artifact_format": ".pt (torch.save: state_dict + config)"
}
```

### Commands

```powershell
C:\Users\Kaustubh\anaconda3\python.exe -m pytest tests/integration/pipeline/test_mlp_training.py -v
C:\Users\Kaustubh\anaconda3\python.exe -m pytest tests/integration/pipeline/ tests/unit/ml/ -q
C:\Users\Kaustubh\anaconda3\python.exe scripts/training/train_mlp.py
```

### Results

Smoke tests only (2 epochs, 1,800 rows). Full-dataset AUC target: above `0.72` on test months 11-12.

### Artifacts

| Artifact | Path |
|---|---|
| MLP training module | `backend/ml/training/neural/train_mlp.py` |
| CLI entrypoint | `scripts/training/train_mlp.py` |
| Smoke tests (6/6) | `tests/integration/pipeline/test_mlp_training.py` |
| Artifact (offline, not checked in) | `models/artifacts/mlp_best.pt` |

### Interpretation

`.pt` save/load round-trip validated: loaded model produces bit-identical probabilities. MLP metrics merge into `metrics.json` and `population_percentiles.json` without dropping TabNet, classical, or baseline entries. Track B (neural) is now fully complete.

### Decision

- Promote: no
- Continue: yes
- Stop: no
- Follow-up: ~~proceed to Track C~~ — done. Proceed to Track D (explainability refresh + manifest promotion for the calibrated ensemble).

## EXP-20260515-010 - Calibrated stacking ensemble (Track C)

- Status: completed
- Owner: Antigravity / Codex
- Date started: 2026-05-15
- Date completed: 2026-05-15
- Branch / commit: `antigravity/dev`
- Related decision: ensemble + calibration track (Track C), offline-training-separation, temporal-split integrity
- Related issue / task: Calibrated stacking ensemble — meta-learner, isotonic calibration, metrics merge, 6 smoke tests

### Hypothesis

If a `LogisticRegression` meta-learner is fitted on the stacked validation-month probability outputs of all 6 base models (logistic, RF, XGBoost, LightGBM, TabNet, MLP) and then wrapped in `CalibratedClassifierCV(method='isotonic', cv='prefit')` on the same fold, the calibrated ensemble will pass a full 6-test smoke suite and merge cleanly into the existing metrics/percentile reports without dropping any prior row.

### Dataset / Feature Set

- Validation fold (meta-features): months `9-10` probability outputs from all 6 base models
- Test fold (held out): months `11-12`
- Meta-feature matrix shape: `(n_val, 6)` — one column per base model in `BASE_MODEL_ORDER`

### Model / Pipeline Configuration

```json
{
  "model_name": "calibrated_stacking",
  "base_model_order": ["logistic_regression","random_forest","xgboost","lightgbm","tabnet","residual_mlp"],
  "meta_learner": {"class": "LogisticRegression", "C": 1.0, "solver": "lbfgs", "max_iter": 1000},
  "calibration": {"method": "isotonic", "cv": "prefit"},
  "artifact_format": ".pkl (joblib CalibratedClassifierCV) + calibrated_stacking_config.json sidecar"
}
```

### Commands

```powershell
C:\Users\Kaustubh\anaconda3\python.exe -m pytest tests/integration/pipeline/test_stacking_training.py -v
C:\Users\Kaustubh\anaconda3\python.exe -m pytest tests/integration/pipeline/ tests/unit/ml/ -q
C:\Users\Kaustubh\anaconda3\python.exe scripts/training/train_stacking.py
```

### Results

Smoke tests only (using pre-computed random probability arrays; test 2 exercises the full 6-base-model pipeline with 2-epoch neural patches).
Full regression suite: 93/93 passing.

### Artifacts

| Artifact | Path |
|---|---|
| Stacking ensemble module | `backend/ml/training/ensemble/train_stacking.py` |
| CLI entrypoint | `scripts/training/train_stacking.py` |
| Smoke tests (6/6) | `tests/integration/pipeline/test_stacking_training.py` |
| Artifact (offline, not checked in) | `models/artifacts/calibrated_stacking.pkl` |
| Config sidecar (offline) | `models/artifacts/calibrated_stacking_config.json` |

### Interpretation

`.pkl` round-trip validated: loaded model produces bit-identical probabilities. Stacking metrics merge into `metrics.json` and `population_percentiles.json` without dropping any prior rows. The `default_model_name` is updated to the model with the highest test AUC. Track C (ensemble + calibration) is fully complete. The calibrated stacking ensemble is the first genuine production-candidate artifact.

### Decision

- Promote: pending (requires SHAP, DICE, fairness refresh and manifest update — Track D)
- Continue: yes
- Stop: no
- Follow-up: Track D — refresh SHAP, DICE, and fairness artifacts against the calibrated ensemble candidate; update `production_manifest.json` to promote it; validate the serving bundle end-to-end.
