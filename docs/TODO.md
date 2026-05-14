# AlterScore TODO

## Current Phase

Repository integrity remediation after merges/refactors is now landed for the checked-in runtime bundle. The canonical feature registry, project hygiene files, backend runtime helpers, API schemas, frontend package skeleton, the synthetic data generation/validation foundation, the local NLP extraction foundation, the preprocessing/split-integrity foundation, the answer-parsing/derived-feature foundation, the behavioral/request-assembly foundation, the dataset materialization command, the baseline training loop, the bounded classical training loop, the persisted text PCA artifact foundation, the runtime artifact-loading plus scoring-service stubs, the FastAPI startup with health/score/all current analytics routes, and the persisted evaluation plus fairness/drift/global-importance artifact foundations for curves, confusion, population percentiles, held-out subgroup fairness, train-vs-test feature stability, and dashboard-ready feature ranking are implemented. `/api/score` now uses the loaded SHAP artifact for per-user explanations and the persisted checked-in `dice_explainer.pkl` artifact for counterfactual actions.

## Immediate TODO

- [x] Reconcile all project docs with the post-merge audit findings before further feature work.
- [x] Restore the missing `backend/ml/explainability/shap_explainer.py` source expected by the checked-in `models/explainers/shap_explainer.pkl`.
- [x] Keep the checked-in `models/explainers/shap_explainer.pkl` artifact for now and validate it from repository source rather than removing it; defer regeneration until richer score-time explainability work lands.
- [x] Regenerate or adapt `models/reports/global_importance.json` so it matches the active `GlobalImportanceResponse` contract.
- [x] Verify and repair the default runtime request-log path so score-request logging works locally; the default now resolves to `runtime/logs/requests.jsonl`.
- [x] Add a fast checked-in artifact-bundle smoke test that validates the local runtime bundle without retraining models in every test case.
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
- [x] Implement `/api/fairness-report`, `/api/drift-report`, and `/api/global-importance` from persisted report files.
- [ ] Finalize production-bundle behavior for manifest-backed serving after explainability runtime stabilizes.
- [x] Make runtime readiness/health checks distinguish between artifact presence and successful optional-artifact deserialization.
- [x] Load and validate SHAP/DICE explainers explicitly when present, and report missing versus invalid optional explainers separately.
- [x] Wire the loaded SHAP explainer into `/api/score`.
- [x] Persist and validate a checked-in `dice_explainer.pkl` so `/api/score` returns artifact-backed counterfactual actions from the default bundle.
- [ ] Decide whether future production bundles should keep the lightweight persisted counterfactual contract or migrate to a richer `dice_ml`-backed artifact after manifest promotion.

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
- [x] Persist `models/reports/population_percentiles.json` from scored offline population predictions.
- [x] Save offline ROC, PR, calibration, and confusion payloads into `models/reports/metrics.json`.
- [x] Persist `models/reports/fairness_report.json` from held-out months `11-12` using protected attributes only for subgroup evaluation.
- [x] Persist `models/reports/psi_report.json` from train months `1-8` vs test months `11-12` using the canonical 35 model inputs only.
- [ ] Train TabNet.
- [ ] Train MLP.
- [ ] Train stacking ensemble.
- [ ] Calibrate stacking ensemble with isotonic regression.
- [ ] Refresh the evaluation bundle again after the future ensemble/calibration path exists.

## Explainability TODO

- [ ] Build SHAP explainer using the selected explainable model path.
- [x] Generate global SHAP importance JSON.
- [ ] Generate SHAP summary plot.
- [x] Implement per-user top factor formatting.
- [x] Persist the current counterfactual artifact and keep the bounded runtime fallback only as a non-default contingency for intentionally artifact-less tests or bundles.
- [x] Build the current counterfactual data/model interface for the checked-in runtime bundle.
- [x] Generate the checked-in `models/explainers/dice_explainer.pkl` artifact.
- [x] Validate that persisted counterfactual actions exclude protected and immutable fields.
- [ ] Evaluate whether to replace the lightweight persisted counterfactual contract with a fuller `dice_ml` object after manifest promotion.

## Fairness And Drift TODO

- [x] Generate fairness report across four protected attributes.
- [x] Add subgroup sample-size guard.
- [x] Compute demographic parity.
- [x] Compute equalized odds.
- [ ] Compute calibration parity data.
- [ ] Compute individual fairness proxy.
- [x] Generate PSI report for train vs months 11-12 test.
- [x] Add dashboard-ready statuses to the fairness report.

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
- [x] Add API integration coverage for `/api/fairness-report`, `/api/drift-report`, and `/api/global-importance`, including missing-report behavior.
- [x] Add integration coverage for offline evaluation artifacts, runtime percentile-table selection, and persisted-dataset training without raw Q27 text.
- [x] Add API integration coverage for `/api/score-distribution`, including missing-artifact behavior.
- [x] Add API integration coverage for `/api/roc-data`, `/api/pr-curve`, `/api/calibration-curve`, and `/api/confusion-matrix`, including missing-artifact behavior.
- [ ] Add integration tests for broader data pipeline steps beyond generator validation and preprocessing split integrity.
- [x] Add integration tests that exercise the checked-in local runtime bundle directly, including the actual saved `global_importance.json` and request-log path behavior.
- [ ] Add E2E tests for assessment and dashboard.

## Deployment TODO

- [x] Document local setup.
- [x] Add backend run command.
- [x] Add frontend run command.
- [ ] Add Docker plan after local app works.
- [x] Add artifact bundle checklist.
- [x] Add health check and rollback plan.
