# Targeted TabNet Repair Experiment

Date: 2026-05-22

## Scope

This was a TabNet-only retraining and dataset-repair experiment. It did not retrain
the full stack and did not replace production artifacts. The existing runtime
TabNet disagreement mitigation remains enabled as the production safeguard.

## Confirmed Repairs

Synthetic target generation was repaired in `backend/ml/data_generation/generator.py`:

- `scroll_hesitation_score` is now generated as higher hesitation / friction, not as a proxy for discipline.
- `engagement_score` now uses `(1 - scroll_hesitation_score)`.
- The direct repayment-label bonus for `device_type == "desktop"` was removed.
- Candidate TabNet training neutralizes `device_type` and `time_of_day` to `mobile` / `afternoon` before preprocessing.

The schema documentation was updated so `device_type` and `time_of_day` are treated as raw telemetry that is neutralized before scoring.

## Dataset Audit

The repaired generator preserved the overall repayment/default mix while fixing directional corruption.

| Audit Item | Before | After |
|---|---:|---:|
| Repayment rate | 0.6962 | 0.6968 |
| Default rate | 0.3038 | 0.3032 |
| `scroll_hesitation_score` label correlation | +0.3469 | -0.3472 |
| `engagement_score` label correlation | +0.3773 | +0.3814 |
| `device_type_desktop` label correlation | +0.0187 | +0.0008 |
| Strong-profile repayment rate | 1.0000 | 1.0000 |
| Strong-profile mean hesitation | 0.7868 | 0.1418 |
| Strong-profile mean engagement | 0.5174 | 0.5617 |

Repaired high-signal subgroup repayment rates remained sensible:

- `resilience_heavy`: 0.8170
- `numeracy_heavy`: 0.9130
- `future_heavy`: 0.9251

## Candidate Runs

All candidates used the production preprocessor and production text PCA for plug-in compatibility. Operational metadata was neutralized before transform/training.

| Candidate | Hyperparameters | Test AUC | Brier | ECE | Disagreement Trigger Rate | Promotion |
|---|---|---:|---:|---:|---:|---|
| Default repaired TabNet | `n_d=16`, `n_a=16`, `n_steps=3`, `gamma=1.3` | 0.7797 | 0.1582 | 0.0253 | 0.0044 | Failed |
| Constrained TabNet | `n_d=8`, `n_a=8`, `n_steps=2`, `gamma=1.0` | 0.7949 | 0.1550 | 0.0255 | 0.0022 | Failed |
| Minimal TabNet | `n_d=4`, `n_a=4`, `n_steps=1`, `gamma=1.0` | 0.7914 | 0.1558 | 0.0359 | 0.0000 | Failed |

Reference old TabNet on repaired labels:

- AUC: 0.7975
- Brier: 0.1554
- ECE: 0.0314

## Monotonic Gates

The promotion gate blocked all candidates.

Default repaired TabNet failed badly on:

- `numeracy_score`
- `scroll_hesitation_score`
- `engagement_score`
- `text_agency_score`
- `conscientiousness_score`
- `repayment_intention_score`
- `psychological_credit_index`

Constrained TabNet reduced the pathology but still failed endpoint gates on:

- `numeracy_score`
- `scroll_hesitation_score`
- `conscientiousness_score`
- `repayment_intention_score`

Minimal TabNet passed endpoint direction checks except one local instability:

- `scroll_hesitation_score` endpoint delta was directionally correct at `-0.0403`
- local step still spiked upward by `+0.2742`, so it failed promotion

This is an important distinction: lower-capacity TabNet improved robustness, but the remaining high-hesitation local bounce is still not acceptable for a credit scoring component.

## Calibration Audit

Calibration was not the root cause of the remaining failures.

For the minimal candidate:

- Raw test AUC: 0.7914
- Raw Brier: 0.1558
- Raw ECE: 0.0359
- Platt Brier: 0.1551
- Platt ECE: 0.0276
- Isotonic hurt AUC and Brier slightly

Calibration can improve probability fit a little, but it does not correct local feature-direction reversals.

## Ensemble Compatibility

No repaired candidate was allowed to re-enter the ensemble because none passed standalone raw TabNet monotonic gates.

This preserves the rule: ensemble re-entry can only be evaluated after a standalone TabNet candidate is behaviorally sane. The current production runtime guard remains the safety layer for the existing artifact.

## Generated Artifacts

Full run reports and plots were written locally:

- `runtime/research_archive/tabnet_repair/baseline/tabnet_repair_experiment_report.json`
- `runtime/research_archive/tabnet_repair/constrained/tabnet_repair_experiment_report.json`
- `runtime/research_archive/tabnet_repair/minimal/tabnet_repair_experiment_report.json`
- `runtime/research_archive/tabnet_repair/*/plots/*_sensitivity.svg`

Candidate model artifacts were written under each run's `runtime/.../artifacts/` directory for inspection only. None were promoted to `models/artifacts/`.

## Root Cause

The original pathology came from corrupted synthetic supervision:

- high hesitation was encoded as higher engagement
- strong profiles also had high synthetic hesitation
- desktop carried a direct repayment bonus
- TabNet learned localized shortcuts from those correlations

AUC alone failed because those shortcuts were useful on the corrupted synthetic distribution. They were not valid under controlled counterfactual profiles.

## Recommendation

Do not promote any repaired TabNet candidate yet. The next safe step is a constrained monotonic training design, not full-stack retraining:

- add true monotonic regularization or monotonic post-processing around `scroll_hesitation_score`
- consider feature masking/suppression for brittle derived composites in TabNet only
- add counterfactual/curriculum balancing rows with explicit monotonic acceptance labels
- only then re-run the same acceptance gates
- only after standalone gates pass, evaluate ensemble variants
