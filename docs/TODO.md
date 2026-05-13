# AlterScore TODO

## Current Phase

Baseline training foundation. The canonical feature registry, project hygiene files, backend runtime helpers, API schemas, frontend package skeleton, the synthetic data generation/validation foundation, the local NLP extraction foundation, the preprocessing/split-integrity foundation, the answer-parsing/derived-feature foundation, the behavioral/request-assembly foundation, the dataset materialization command, and the first baseline training loop are implemented; app runtime and API routes are not started.

## Immediate TODO

- [x] Add mandatory AI workflow rules for startup, documentation updates, testing, git, and session close.
- [x] Implement the canonical 35-input feature registry before writing data generator code.
- [x] Add `.gitignore` for generated data, model artifacts, logs, env files, caches, and node/python build outputs.
- [x] Add `.env.example`.
- [x] Add backend dependency file with pinned Python package versions.
- [x] Implement feature registry constants.
- [x] Implement API schemas.
- [x] Add feature registry tests.
- [x] Add schema tests.
- [x] Add frontend package skeleton.
- [x] Implement synthetic data generator and validation foundation.

## Documentation TODO

- [x] Keep `docs/CURRENT_STATE.md` updated after each task.
- [ ] Add decision entries for any architecture changes.
- [ ] Add detailed ADR files under `docs/adr/` when a decision becomes too large for `docs/DECISIONS.md`.
- [ ] Update `docs/API_CONTRACTS.md` when schemas change.
- [ ] Update `docs/DATA_SCHEMA.md` when features change.
- [ ] Update `docs/MODEL_REGISTRY.md` after any model training or artifact promotion.
- [ ] Update `docs/EXPERIMENT_LOG.md` after every training experiment.

## Backend TODO

- [x] Create settings and path modules.
- [ ] Create artifact loader with clear missing-artifact errors.
- [x] Create Pydantic schemas for score requests and responses.
- [x] Create Pydantic schemas for analytics responses.
- [ ] Create route stubs only after schemas exist.
- [ ] Implement request logging service.
- [ ] Implement health endpoint.
- [ ] Implement scoring endpoint after inference pipeline is ready.
- [ ] Implement analytics endpoints after reports exist.

## Data Pipeline TODO

- [x] Implement correlated psychometric feature generation.
- [x] Implement behavioral feature generation.
- [x] Implement realistic demographic generation.
- [x] Implement cohort month assignment and temporal drift.
- [x] Implement latent label generation with target default rate.
- [x] Save raw synthetic dataset.
- [x] Implement validation report.
- [x] Implement in-memory validation helpers for row count, nulls, default rate, cohort bounds, and feature-list separation.
- [x] Add tests for default rate, documented temporal split intent, missing values, and protected separation.
- [x] Add explicit train/validation/test split mask integrity tests once split helpers exist.

## NLP TODO

- [x] Pin sentence-transformer model name.
- [x] Pin spaCy model name.
- [x] Implement neutral fallback for empty/short text.
- [x] Implement VADER sentiment feature.
- [x] Implement agency score feature.
- [x] Implement problem-solving flag.
- [x] Implement embedding extraction.
- [x] Fit PCA only on train embeddings.
- [x] Add high-agency and low-agency tests from PRD.

## Feature Engineering TODO

- [x] Implement answer parser.
- [x] Implement behavioral parser.
- [x] Implement raw-request feature assembly helper.
- [x] Implement derived feature calculations.
- [x] Define actionable feature list for counterfactuals.
- [x] Define immutable feature list.
- [x] Add known-payload tests for parsed features.

## ML Training TODO

- [x] Implement preprocessing pipeline.
- [x] Implement explicit temporal split integrity checks.
- [x] Fit text PCA on train months 1-8 only.
- [x] Implement majority baseline.
- [x] Implement logistic baseline.
- [x] Implement simulated loan officer comparator.
- [ ] Train random forest.
- [ ] Train XGBoost.
- [ ] Train LightGBM.
- [ ] Train TabNet.
- [ ] Train MLP.
- [ ] Train stacking ensemble.
- [ ] Calibrate stacking ensemble with isotonic regression.
- [ ] Generate metrics and curves.

## Explainability TODO

- [ ] Build SHAP explainer using the selected explainable model path.
- [ ] Generate global SHAP importance JSON.
- [ ] Generate SHAP summary plot.
- [ ] Implement per-user top factor formatting.
- [ ] Build DICE data/model interface.
- [ ] Generate DICE explainer artifact.
- [ ] Validate DICE actions exclude protected and immutable fields.

## Fairness And Drift TODO

- [ ] Generate fairness report across four protected attributes.
- [ ] Add subgroup sample-size guard.
- [ ] Compute demographic parity.
- [ ] Compute equalized odds.
- [ ] Compute calibration parity data.
- [ ] Compute individual fairness proxy.
- [ ] Generate PSI report for train vs months 11-12 test.
- [ ] Add dashboard-ready statuses.

## Frontend TODO

- [x] Create React app skeleton.
- [ ] Add design tokens.
- [ ] Add question data exactly from PRD after API schema is stable.
- [ ] Build assessment flow and telemetry.
- [ ] Build results page.
- [ ] Build score gauge.
- [ ] Build factor bars.
- [ ] Build counterfactual actions.
- [ ] Build share card export.
- [ ] Build dashboard components after analytics endpoints exist.
- [ ] Add mobile QA and browser checks.

## Testing TODO

- [x] Add unit tests for schemas.
- [x] Add unit tests for feature registry.
- [x] Add integration coverage for synthetic data generation validation and determinism.
- [x] Add unit tests for NLP extraction, neutral fallback, PRD high/low agency examples, and raw embedding determinism.
- [x] Add integration tests for preprocessing split integrity, train-only PCA fitting, and sklearn transform shape/imputation behavior.
- [x] Add unit tests for answer parser.
- [x] Add unit tests for behavioral parser.
- [x] Add unit tests for derived features.
- [x] Add integration coverage for raw-request feature assembly through NLP PCA and preprocessing compatibility.
- [x] Add integration coverage for dataset materialization and baseline training artifacts.
- [ ] Add integration tests for broader data pipeline steps beyond generator validation and preprocessing split integrity.
- [ ] Add integration tests for API endpoints.
- [ ] Add E2E tests for assessment and dashboard.
- [ ] Add smoke test for artifact loading.

## Deployment TODO

- [ ] Document local setup.
- [ ] Add backend run command.
- [ ] Add frontend run command.
- [ ] Add Docker plan after local app works.
- [ ] Add artifact bundle checklist.
- [ ] Add health check and rollback plan.
