# AlterScore TODO

## Current Phase

Frontend package foundation. The canonical feature registry, project hygiene files, backend runtime helpers, API schemas, and frontend package skeleton are implemented; app runtime, data generation, training, and API routes are not started.

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

- [ ] Implement correlated psychometric feature generation.
- [ ] Implement behavioral feature generation.
- [ ] Implement realistic demographic generation.
- [ ] Implement cohort month assignment and temporal drift.
- [ ] Implement latent label generation with target default rate.
- [ ] Save raw synthetic dataset.
- [ ] Implement validation report.
- [ ] Add tests for default rate, split integrity, missing values, and protected separation.

## NLP TODO

- [ ] Pin sentence-transformer model name.
- [ ] Pin spaCy model name.
- [ ] Implement neutral fallback for empty/short text.
- [ ] Implement VADER sentiment feature.
- [ ] Implement agency score feature.
- [ ] Implement problem-solving flag.
- [ ] Implement embedding extraction.
- [ ] Fit PCA only on train embeddings.
- [ ] Add high-agency and low-agency tests from PRD.

## Feature Engineering TODO

- [ ] Implement answer parser.
- [ ] Implement behavioral parser.
- [ ] Implement derived feature calculations.
- [x] Define actionable feature list for counterfactuals.
- [x] Define immutable feature list.
- [ ] Add known-payload tests for parsed features.

## ML Training TODO

- [ ] Implement preprocessing pipeline.
- [ ] Implement majority baseline.
- [ ] Implement logistic baseline.
- [ ] Implement simulated loan officer comparator.
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
- [ ] Add unit tests for answer parser.
- [ ] Add unit tests for derived features.
- [ ] Add unit tests for NLP.
- [ ] Add integration tests for data pipeline.
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
