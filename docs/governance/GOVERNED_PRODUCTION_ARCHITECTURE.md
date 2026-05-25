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
[scripts/train_monotonic_tree_candidates.py](C:/Kaustubh/Projects/AlterScore/scripts/train_monotonic_tree_candidates.py).

This superseded the earlier production ensemble as the default runtime while
keeping the ensemble artifacts available for benchmark and rollback/reference
work.

## Current Production Candidate

The current active governed production runtime is monotonic `XGBoost`.

The latest full-scale governed comparison and fairness-hardening review showed:

- monotonic `XGBoost` materially outperformed the former runtime ensemble in
  the governed full-run review
- it clears the monotonic, counterfactual, and fairness promotion gates
- conservative fairness-hardening variants can reduce small-subgroup
  calibration error somewhat, but the baseline raw monotonic `XGBoost`
  remained the preferred operating point in that review

The checked-in promoted bundle is the operational source of truth. Its current
reports show AUC `0.8040`, Brier `0.1514`, ECE `0.0284`, stable PSI, and a
fairness attention item for `gender=non_binary`; that item must be reconciled
before pilot claims.

This is an important architecture outcome:

- governance-aware validation changed the preferred production system
- aggregate AUC alone was not enough to trust earlier high-capacity models
- constrained monotonic tree systems currently provide the best balance of
  predictive strength, behavioral stability, fairness control, and deployment
  reliability
