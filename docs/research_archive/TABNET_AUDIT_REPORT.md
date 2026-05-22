# TabNet Audit Report

Date: 2026-05-22

## Scope

This audit focused on the live TabNet base model only, not a full-stack retrain.

It covered:

- training-distribution analysis on the synthetic dataset
- local one-feature sensitivity sweeps against the current TabNet artifact
- post-hoc calibration checks for standalone TabNet
- implications for constrained retraining

## Confirmed Findings

### 1. Raw TabNet is already pathological before ensemble stacking

This is not primarily a meta-learner or isotonic-stacking problem.

Against a fixed strong anchor profile, raw TabNet probability collapses as several economically positive features increase:

- `future_orientation: 0.0 -> 1.0` gives roughly `0.95 -> 0.04`
- `resilience_score: 0.0 -> 1.0` gives roughly `0.89 -> 0.04`
- `scroll_hesitation_score: 0.0 -> 1.0` gives roughly `0.04 -> 0.98`

That means the monotonic failures are already present in the raw TabNet response surface.

### 2. Standalone post-hoc calibration does not solve the pathology

Validation split:

- raw AUC: `0.7905`
- isotonic AUC: `0.7983`
- platt AUC: `0.7905`

Test split:

- raw AUC: `0.7889`
- isotonic AUC: `0.7835`
- platt AUC: `0.7889`

Test-set Brier:

- raw: `0.1579`
- isotonic: `0.1595`
- platt: `0.1570`

So:

- isotonic helps on validation but hurts held-out test
- platt gives a small Brier improvement but does not change ranking
- neither calibration fixes the monotonic reversals

Conclusion: calibration alone is insufficient.

### 3. Synthetic training labels contain known bad correlations

The synthetic generator still encodes:

- the old `engagement_score` polarity where higher `scroll_hesitation_score` increases engagement
- a direct positive repayment bonus for `device_type == desktop`

These correlations are present in the checked-in dataset that trained TabNet.

Observed label correlations in `synthetic_dataset.csv`:

- `scroll_hesitation_score` vs `repayment_label`: `+0.3469`
- `engagement_score` vs `repayment_label`: `+0.3773`
- `device_type_desktop` vs `repayment_label`: positive

This is strong evidence that TabNet learned from corrupted supervision, not just noisy inference features.

### 4. Strong profiles in the synthetic data are themselves skewed toward the bad pattern

For rows with high numeracy, high future orientation, and high resilience:

- repayment rate is `1.0`
- average `scroll_hesitation_score` is about `0.787`
- average synthetic `engagement_score` is high

That means “strong” synthetic rows were often generated with the same high-hesitation pattern that the runtime logic now treats as undesirable.

This train-vs-runtime mismatch is especially risky for TabNet because it can learn sharp nonlinear partitions.

## Interpretation

The current TabNet artifact appears to be learning a decision surface shaped by:

1. corrupted synthetic-label logic
2. noisy metadata exposure
3. nonlinear interactions that saturate into near-binary pockets

That explains why TabNet:

- performs acceptably on aggregate AUC
- but fails catastrophically on localized monotonic audits

## Recommended Next Step

Do not retrain the full ensemble yet.

Run a targeted TabNet retraining experiment with these constraints:

1. regenerate or repair the synthetic training target logic first
2. remove `device_type` and `time_of_day` from TabNet training inputs
3. retrain TabNet alone
4. evaluate raw TabNet monotonic sweeps before any stacking
5. only then test whether the refreshed TabNet should re-enter the ensemble

## Suggested Constrained Retraining Options

Highest priority:

- repair synthetic target generation to use the corrected engagement logic
- suppress operational metadata from TabNet inputs
- rebalance training samples for high numeracy / high resilience / high future-orientation regions

Worth testing:

- stronger feature clipping on unstable behavioral composites
- reduced capacity / regularization for TabNet to limit brittle partitions
- monotonic audit gating during model acceptance

Lower confidence for this repo as-is:

- post-hoc calibration alone
- keeping the current dataset unchanged and only retuning TabNet hyperparameters

## Operational Recommendation

Until targeted TabNet retraining is complete:

- keep the runtime TabNet disagreement mitigation enabled
- keep `/api/debug-score` enabled in audit environments
- continue using the controlled monotonic audit cases before promoting any updated artifact
