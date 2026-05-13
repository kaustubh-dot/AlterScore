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

No experiments have been run yet.

