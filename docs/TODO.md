# AlterScore TODO

## Current Phase

First analytics endpoints. The canonical feature registry, project hygiene files, backend runtime helpers, API schemas, frontend package skeleton, the synthetic data generation/validation foundation, the local NLP extraction foundation, the preprocessing/split-integrity foundation, the answer-parsing/derived-feature foundation, the behavioral/request-assembly foundation, the dataset materialization command, the baseline training loop, the bounded classical training loop, the persisted text PCA artifact foundation, the runtime artifact-loading plus scoring-service stubs, the first FastAPI startup with health/score/model-stats/baseline-comparison routes, and append-only request logging are implemented; the remaining analytics routes and full production-runtime artifacts are not started.

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
- [x] Create artifact loader with clear missing-artifact errors.
- [x] Create backend scoring service stubs against saved runtime artifacts.
- [x] Create Pydantic schemas for score requests and responses.
- [x] Create Pydantic schemas for analytics responses.
- [x] Wire FastAPI startup artifact caching.
- [x] Add `/api/health` route stub backed by artifact status.
- [x] Add `/api/score` route stub backed by the scoring service.
- [x] Create route stubs only after schemas exist.
- [x] Implement request logging service.
- [x] Implement health endpoint.
- [x] Add report-backed analytics service foundation and the first `/api/model-stats` plus `/api/baseline-comparison` endpoints.
- [ ] Harden the scoring endpoint with explainability, counterfactual, and production-bundle behavior.
- [ ] Implement the remaining analytics endpoints after their backing reports exist.

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
- [x] Train random forest.
- [x] Train XGBoost.
- [x] Train LightGBM.
- [x] Persist `models/preprocessors/text_pca.pkl` for runtime semantic projection.
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
- [x] Add integration coverage for classical model training artifacts, probability bounds, and metrics merging.
- [x] Add score-mapper unit coverage.
- [x] Add artifact-loading and scoring-smoke coverage against saved runtime artifacts.
- [x] Add API integration tests for `/api/health` and `/api/score` stubs.
- [x] Add API integration coverage for request logging on `/api/score`.
- [x] Add integration coverage for persisted text PCA artifacts, runtime semantic projections, and intentional zero-fill fallback behavior.
- [x] Add API integration coverage for `/api/model-stats` and `/api/baseline-comparison`, including missing-report behavior.
- [ ] Add integration tests for broader data pipeline steps beyond generator validation and preprocessing split integrity.
- [ ] Add integration tests for the remaining analytics endpoints.
- [ ] Add E2E tests for assessment and dashboard.

## Deployment TODO

- [x] Document local setup.
- [x] Add backend run command.
- [x] Add frontend run command.
- [ ] Add Docker plan after local app works.
- [x] Add artifact bundle checklist.
- [x] Add health check and rollback plan.
