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
