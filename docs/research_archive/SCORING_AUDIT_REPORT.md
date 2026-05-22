# Scoring Audit Report

Date: 2026-05-22

## Scope

This audit traced the live scoring path end to end:

- frontend answer construction
- behavioral telemetry payload
- backend request validation
- feature assembly
- preprocessing
- ensemble inference
- calibration
- score mapping
- frontend result rendering

Temporary instrumentation was added through:

- `POST /api/debug-score`
- backend scoring trace generation in `backend/app/services/scoring.py`
- `scripts/audit_scoring_pipeline.py`

## Confirmed Bugs

### 1. `engagement_score` polarity is inverted

File: `backend/ml/features/derived_features.py`

`engagement_score` currently multiplies by `scroll_hesitation_score`, so more hesitation increases engagement:

```python
engagement_score = scroll_hesitation_score * ...
```

Observed runtime behavior:

- `scroll_hesitation_score=0.05` -> score `718`
- `scroll_hesitation_score=0.95` -> score `850`

Severity: P0

### 2. Percentile artifact does not match the runtime ensemble

Files:

- `models/registry/production_manifest.json`
- `models/reports/population_percentiles.json`

The runtime model is `stacking_ensemble`, but `population_percentiles.json` only contains `logistic_regression`.

Observed:

- manifest runtime model: `stacking_ensemble`
- percentile payload available models: `["logistic_regression"]`

This means percentile output is currently derived from the wrong score distribution.

Severity: P1

### 3. Stronger text can score the same as empty text

Files:

- `backend/ml/nlp/extractor.py`
- `backend/app/services/scoring.py`

Observed:

- empty resilience text -> score `754`
- strong action-oriented text -> score `746`
- missing-text case from controlled audit -> same or better than stronger text

The current text pipeline is not reliably rewarding stronger borrower narratives.

Severity: P1

### 4. NLP sentiment heuristics misclassify obviously negative text as positive

File: `backend/ml/nlp/extractor.py`

Observed:

- negative text: `"Everything fell apart... unable to do anything..."` produced:
  - `text_sentiment_compound = 0.5423`

That is a clear directional error in sentiment extraction.

Severity: P1

### 5. Device and time-of-day materially affect score

Files:

- `backend/ml/preprocessing/feature_registry.py`
- model artifacts

Observed:

- `device_type=mobile` -> score `746`
- `device_type=desktop` -> score `830`
- `time_of_day=morning` -> score `739`
- `time_of_day=night` -> score `729`

These effects are too large for operationally noisy metadata and create fairness and stability risk.

Severity: P1

## Confirmed Monotonicity Violations

These were measured against the checked-in runtime ensemble with the new debug trace.

### Better numeracy reduced score

- low numeracy -> score `754`
- high numeracy -> score `746`

### Better future orientation reduced score

- low future orientation -> score `754`
- high future orientation -> score `746`

### Better resilience reduced score

- low resilience -> score `850`
- high resilience -> score `746`

### Higher scroll hesitation improved score

- low hesitation -> score `718`
- high hesitation -> score `850`

### Lower text quality did not consistently hurt score

- empty text -> score `754`
- strong text -> score `746`

## Model Behavior Notes

These do not look like request-contract bugs. The frontend and backend field names are aligned, and answer indexing is consistent with the backend schema.

The strongest evidence points to a mix of:

- one confirmed feature-engineering bug
- artifact/report mismatch
- learned model behavior that is not economically monotonic
- noisy metadata being over-weighted

One especially important clue:

- for high numeracy and high resilience cases, the TabNet base model collapses to a very low positive probability while the other base models remain strong

This suggests at least part of the reversal is coming from trained artifact behavior, not just the post-processing code.

## Missing Product-Critical Inputs

The current live feature set does **not** include direct borrower financial fields such as:

- income
- debt
- savings
- employment stability
- EMI burden
- prior repayment history

So requirements like:

- higher income should generally not reduce score
- lower debt should generally improve score
- higher savings should improve score
- stable employment should improve score

cannot actually be validated in the live product, because those inputs are not present in the scoring contract at all.

This is a model-scope gap, not just a bug.

## Artifact / Environment Notes

The checked-in runtime ensemble was serialized with `scikit-learn 1.8.x`.

An existing local Conda environment with `scikit-learn 1.5.1` could not load the ensemble artifact because it depends on `sklearn.frozen.FrozenEstimator`.

To complete the live audit, a dedicated local runtime env was created at:

- `backend/.venv-score-debug`

with the pinned backend dependencies.

## Added Debugging Tools

### API

- `POST /api/debug-score`

Returns:

- raw input
- validated request
- psychometric features
- behavioral features
- NLP features
- transformed feature vector
- categorical encodings
- base model outputs
- meta-feature vector
- calibrated probabilities
- score mapping details
- final score outputs

### Script

- `scripts/audit_scoring_pipeline.py`

This runs controlled test cases and monotonic checks against the current bundle.

## Recommended Fix Order

### Immediate

1. Fix `engagement_score` polarity.
2. Rebuild `population_percentiles.json` for the ensemble runtime model.
3. Reduce or remove `device_type` and `time_of_day` influence from the production path unless explicitly justified.
4. Keep `/api/debug-score` enabled during the audit/fix cycle.

### Next

5. Audit the TabNet artifact specifically, because it is a consistent outlier in several strong-profile scenarios.
6. Re-run controlled monotonic checks after fixing the polarity bug.
7. Recompute explanation and counterfactual outputs after model fixes, because they currently recommend changes that do not always improve score.

### Strategic

8. Add actual financial state variables to the request contract if the product expects income/debt/savings/employment monotonicity.
9. Add automated monotonic regression tests for critical features before promoting new artifacts.

