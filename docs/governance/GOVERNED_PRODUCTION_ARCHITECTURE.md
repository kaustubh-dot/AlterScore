# Governed Production Architecture

## Direction

AlterScore is now treated as a governed behavioral credit scoring platform for
unbanked users, not just a high-AUC modeling exercise.

Primary production-track priorities:

- predictive strength
- monotonic consistency
- counterfactual stability
- fairness
- explainability
- deployment reliability

## Production Scoring Track

The preferred production-track candidates are constrained tree systems:

- monotonic `LightGBM`
- monotonic `XGBoost`

These candidates should emphasize:

- atomic psychometric features
- behavioral telemetry
- interpretable NLP-derived signals

They should de-emphasize or suppress:

- brittle high-order composite features
- opaque nonlinear interaction-heavy features
- operational metadata such as `device_type` and `time_of_day`

## Research Track

TabNet remains valuable, but it is now positioned as:

- research benchmark
- representation-learning comparison
- optional auxiliary ensemble contributor

TabNet is not the default trusted production scorer unless it clears the same
governance requirements as constrained-tree candidates.

## Hard Governance Requirements

Production candidates must satisfy all of the following, not just aggregate AUC:

- temporal validation on months `9-10` and `11-12`
- monotonic sensitivity acceptance gates
- pairwise counterfactual acceptance gates
- subgroup fairness evaluation
- calibration review
- drift reporting
- explainability artifact generation
- production artifact compatibility

## Current Implementation

The constrained-tree production track now has a dedicated feature-policy layer
in [backend/ml/training/classical/monotonic_constraints.py](C:/Kaustubh/Projects/AlterScore/backend/ml/training/classical/monotonic_constraints.py)
and a governed candidate-training entry point in
[scripts/training/train_calibrated_monotonic_xgboost.py](C:/Kaustubh/Projects/AlterScore/scripts/training/train_calibrated_monotonic_xgboost.py).

This superseded the earlier production ensemble as the default runtime while
keeping the ensemble artifacts available for benchmark and rollback/reference
work.

## Current Production Candidate

The current active governed production runtime is calibrated monotonic `XGBoost`.

The latest full-scale governed comparison and fairness-hardening review showed:

- monotonic `XGBoost` materially outperformed the former runtime ensemble in
  the governed full-run review
- it clears the monotonic, counterfactual, and fairness promotion gates
- conservative fairness-hardening variants can reduce small-subgroup
  calibration error somewhat, but the baseline raw monotonic `XGBoost`
  remained the preferred operating point in that review

The checked-in promoted bundle is the operational source of truth. Its current
reports show held-out AUC `0.7787`, ECE `0.0346`, subgroup fairness passing
under the bounded AUC-gap policy, and individual-fairness proxy flagged-pair
share `0.027` with max similar-pair score gap `130` (similarity measured over
the model's active, non-masked features). PSI is `stable` at max `0.0152`,
below the `0.30` alert threshold. Older governed-review figures such as
`0.8040` and `0.8090` are historical experiment/report contexts, not the active
manifest metric.

This is an important architecture outcome:

- governance-aware validation changed the preferred production system
- aggregate AUC alone was not enough to trust earlier high-capacity models
- constrained monotonic tree systems currently provide the best balance of
  predictive strength, behavioral stability, fairness control, and deployment
  reliability
