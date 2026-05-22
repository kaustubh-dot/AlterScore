# Governance Workflow

## Philosophy

AlterScore does not promote production candidates on aggregate AUC alone.

A model is treated as production-ready only if it is:

- predictively strong
- monotonicity-audited
- counterfactually stable
- fairness-reviewed
- calibration-reviewed
- explainable
- operationally reproducible

## Production Candidate Flow

1. Generate or load the evaluation dataset with temporal splits.
2. Train the candidate using the approved production-track feature policy.
3. Evaluate discrimination and calibration on validation and held-out test data.
4. Run monotonic sensitivity audits.
5. Run pairwise counterfactual stability audits.
6. Run subgroup fairness and calibration-parity analysis.
7. Review proxy-sensitive features and subgroup SHAP behavior.
8. Compare against the current runtime baseline.
9. Promote only if all active governance gates pass.

## Hard Gates

The repository currently treats these as hard promotion requirements:

- monotonic acceptance gate
- pairwise counterfactual acceptance gate
- fairness gate
- production bundle compatibility

These thresholds must not be weakened during cleanup or release preparation.

## Production-Track Scripts

Primary governed evaluation scripts:

- [scripts/train_monotonic_tree_candidates.py](C:/Kaustubh/Projects/AlterScore/scripts/train_monotonic_tree_candidates.py)
- [scripts/fairness_harden_xgboost_candidate.py](C:/Kaustubh/Projects/AlterScore/scripts/fairness_harden_xgboost_candidate.py)

Research-only supporting script retained for governance comparison:

- [scripts/retrain_tabnet_repair_experiment.py](C:/Kaustubh/Projects/AlterScore/scripts/retrain_tabnet_repair_experiment.py)

## Promotion Review Standard

Promotion is not justified solely because:

- AUC improves
- calibration improves in one slice
- ranking beats the previous ensemble

Promotion requires the full governance stack to remain green.

## Current Operating Position

The leading governed production candidate is monotonic `XGBoost`.

The current runtime ensemble remains the checked-in baseline until the final
promotion package is approved and released in a deliberate handoff.
