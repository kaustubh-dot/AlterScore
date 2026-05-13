# Experiment Logging Template

Copy this into `docs/EXPERIMENT_LOG.md` for every meaningful ML or data experiment.

## EXP-YYYYMMDD-NNN - Title

- Status: planned | running | completed | failed | superseded
- Owner:
- Date started:
- Date completed:
- Branch / commit:
- Related decision:
- Related issue / task:

### Hypothesis


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

### Fairness Summary

- Worst AUC gap:
- Flagged groups:
- Notes:

### Drift Summary

- Max PSI:
- Top drifted features:
- Verdict:

### Artifacts

| Artifact | Path |
|---|---|

### Interpretation


### Decision

- Promote:
- Continue:
- Stop:
- Follow-up:

