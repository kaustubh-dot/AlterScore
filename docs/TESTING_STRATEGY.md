# AlterScore Testing Strategy

## Testing Principles

- Test feature and schema contracts before model complexity.
- Test leakage prevention explicitly.
- Prefer deterministic small smoke tests for CI and heavier full-pipeline tests for local milestone gates.
- Every dashboard panel needs a backend contract test before frontend work is considered complete.
- ML acceptance is based on temporal test split, not random split.
- Tests that need temporary files should use the workspace-local `tmp_path` fixture override in `tests/conftest.py` so they do not depend on machine-specific permissions under the global Windows temp path.

## Test Layout

```text
tests/
  unit/
    backend/
      test_score_schema.py
      test_analytics_schema.py
      test_settings.py
    frontend/
      test_frontend_skeleton.py
    ml/
      test_feature_registry.py
      test_answer_parser.py
      test_behavioral_parser.py
      test_derived_features.py
      test_score_mapper.py
      test_nlp_features.py
  integration/
    api/
      test_health_endpoint.py
      test_score_endpoint.py
      test_analytics_endpoints.py
    pipeline/
      test_data_generation_validation.py
      test_dataset_artifacts_and_baselines.py
      test_feature_assembly.py
      test_preprocessing_split_integrity.py
      test_artifact_loading.py
  e2e/
    test_assessment_to_results.py
    test_dashboard_loads.py
  fixtures/
    score_request_valid.json
    score_request_low_signal.json
    score_request_high_signal.json
```

## Unit Test Requirements

### Feature Registry

- `PROTECTED_FEATURES` has no overlap with `NUMERIC_FEATURES` or `CATEGORICAL_FEATURES`.
- `TEMPORAL_METADATA` has no overlap with model inputs.
- `TARGET` is not a model input.
- Actionable counterfactual features exclude protected, categorical, temporal, and immutable fields.
- Feature order is stable.

### Answer Parser

- Known correct numeracy answers produce high `numeracy_score`.
- CRT trap answers produce low `CRT_score`.
- Repeated future-orientation inconsistency lowers `honesty_score`.
- Social desirability trap agreement lowers `honesty_score`.
- All required psychometric feature keys are returned.

### Derived Features

- All 7 derived features are computed.
- Values are clipped or bounded where required.
- Higher impulsivity inputs increase `impulsivity_index`.
- Higher engagement inputs increase `engagement_score`.

### Behavioral Parser

- Valid telemetry payloads map to all 9 canonical behavioral features.
- Numeric telemetry fields are clipped to documented bounds.
- Unknown `device_type` and `time_of_day` values are rejected.
- Pydantic behavioral payloads and raw mappings produce equivalent outputs.

### Score Mapper

- Scores stay between 300 and 850.
- Higher repayment probability always produces a score greater than or equal to lower probability.
- Risk bands are stable at documented thresholds.
- Loan eligibility maps to risk bands.

### NLP Features

- Empty text returns neutral defaults.
- High-agency text has higher `text_agency_score` than low-agency text.
- Problem-solving keywords trigger `text_problem_solving_flag`.
- Sentiment compound stays in -1 to 1.
- Raw embedding extraction is deterministic for a fixed text and returns 384 dimensions.

## Data Validation Tests

Required checks after data generation:

- Dataset has 10,000 rows.
- Dataset generation is deterministic for a fixed seed.
- No missing values.
- Default rate is between 24 and 32 percent.
- Cohort months are only 1-12.
- Months 11-12 contain at least 1,000 rows.
- Generated columns include all model features, protected attributes, temporal metadata, and the target.
- Train, validation, and test splits do not overlap.
- `cohort_month` and `application_date` are absent from model feature lists.
- Protected attributes are present for fairness reports but absent from model features.
- Later cohorts show mild response-time and typing-speed drift in the documented direction.
- Primary features have non-trivial relationship with `repayment_label`.
- Protected attributes do not have concerning direct correlation with the label.

## ML Validation Tests

### Model Sanity

```python
assert calibrated_model.predict_proba(X_test).shape == (len(X_test), 2)
assert ((probs >= 0) & (probs <= 1)).all()
```

### Score Range

```python
scores = [probability_to_score(p) for p in probs]
assert all(300 <= s <= 850 for s in scores)
```

### Temporal Split Integrity

```python
assert df.loc[train_idx, "cohort_month"].max() <= 8
assert df.loc[val_idx, "cohort_month"].between(9, 10).all()
assert df.loc[test_idx, "cohort_month"].min() >= 11
assert "cohort_month" not in X_train.columns
```

### Request Feature Assembly

- A validated score request assembles to the canonical `ALL_MODEL_FEATURES` order.
- Protected attributes, temporal metadata, and the target are absent from assembled runtime feature frames.
- Text semantic dimensions come from the train-fitted PCA artifact, not direct request input.
- Assembled request feature frames can be passed into the saved sklearn preprocessor without shape or null issues.

### Dataset Materialization And Baselines

- The dataset command saves `data/raw/synthetic_dataset.csv` and `data/validation/validation_summary.json`.
- The validation summary includes split counts, missing-value counts, numeric stats, and label-correlation diagnostics.
- The baseline training loop saves `preprocessor.pkl`, `logistic_best.pkl`, `baseline_metrics.json`, and `metrics.json`.
- Baseline metrics are ordered as majority class, logistic regression, and simulated loan officer.

### Baseline Lift

```python
assert metrics["ensemble"]["auc_roc"] > metrics["baselines"]["simulated_loan_officer"]["auc_roc"]
```

### SHAP

- SHAP values are not all zero.
- Top factor response includes 6 or fewer items.
- Every factor has `feature`, `display_name`, `shap_value`, `direction`, and `feature_value`.

### DICE

- Generates 1-3 actions for eligible low/mid applicants.
- Does not suggest protected attributes.
- Does not suggest immutable categorical fields.
- Includes plain-language action text.

### PSI

- PSI values are non-negative.
- Report includes max PSI, verdict, top drifted features, and all feature table.

## API Integration Tests

### Health

- `GET /api/health` returns 200.
- Response includes `status`, `version`, `model_loaded`, `artifacts_loaded`, and `missing_artifacts`.

### Score

- Valid payload returns 200.
- Low-signal and high-signal fixtures both return valid JSON.
- `credit_score` is 300-850.
- `repayment_probability` is 0-1.
- `risk_band` is one of documented bands.
- `explanation` is present.
- `counterfactual_actions` is present.
- Protected attributes are absent from response.

### Analytics

Each analytics endpoint must:

- Return 200 after report artifacts exist.
- Return schema-valid JSON.
- Return useful error if the backing report is missing.
- Avoid expensive model retraining during request handling.

## Frontend Tests

### Assessment

- User can complete all 27 questions.
- Required fields prevent invalid submit.
- Telemetry fields are computed.
- Network failure does not lose answers.
- Retry submits the same payload.

### Results

- Missing route state redirects safely.
- Score gauge renders score and band.
- Factor bars render positive and negative directions.
- Counterfactual actions render without overflow.
- Share card export path has fallback behavior.

### Dashboard

- Every chart has loading, error, and success states.
- One failed endpoint does not break the entire dashboard.
- Tables scroll horizontally on mobile.
- Charts fit at 375px width.

## E2E Milestone Tests

- Full assessment to results in a local browser.
- Dashboard loads all panels from backend reports.
- Mobile viewport at 375px remains usable.
- Backend restart reloads artifacts and health remains green.

## Acceptance Gates By Milestone

| Milestone | Required Tests |
|---|---|
| M1 Data Contract | Feature registry, schemas, data validation tests |
| M2 Baseline | NLP, preprocessing, baseline metrics tests |
| M3 Production Candidate | ML sanity, calibration, ensemble lift tests |
| M4 Governance | SHAP, DICE, fairness, PSI tests |
| M5 API | Health, score, analytics integration tests |
| M6 Frontend | Assessment/results/dashboard E2E tests |
| M7 Release | Full smoke suite and deployment health check |
