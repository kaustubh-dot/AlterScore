# AlterScore Roadmap

## Roadmap Principles

- Contracts before implementation.
- Data before training.
- Baselines before advanced models.
- Stable model artifacts before backend inference.
- Backend contracts before frontend integration.
- Analytics data before dashboard visuals.
- Local reproducibility before deployment.

## Recommended Development Order

| Order | Phase | Goal | Exit Criteria |
|---:|---|---|---|
| 0 | Engineering scaffold | Project memory and structure | Docs and folders exist |
| 1 | Contracts and feature registry | Freeze API/data/model interfaces | Schemas documented and tests planned |
| 2 | Data generation | Create valid synthetic dataset | Validation summary passes |
| 3 | NLP pipeline | Local text feature extraction | NLP unit tests pass |
| 4 | Feature engineering and preprocessing | Train/inference feature parity | Preprocessor artifact saved |
| 5 | Baselines and classical models | Establish performance floor | Baseline/classical metrics generated |
| 6 | Neural models | Add TabNet and MLP | Neural metrics generated |
| 7 | Stacking and calibration | Create production candidate | Calibrated ensemble artifact saved |
| 8 | Explainability, fairness, drift, evaluation | Generate dashboard artifacts | Reports generated and validated |
| 9 | FastAPI backend | Serve score and analytics contracts | API tests pass |
| 10 | React assessment/results | Complete borrower scoring flow | E2E assessment flow passes |
| 11 | React dashboard | Complete evaluator analytics | Dashboard loads all reports |
| 12 | Polish and deployment | Demo-ready production packaging | Release checklist passes |

## Exact Near-Term Implementation Steps

0. [x] Complete the repository integrity remediation pass: reconcile docs, repair the checked-in SHAP artifact/module path, regenerate or adapt the checked-in global-importance artifact, and verify the default runtime request-log path.
1. [x] Create `.gitignore`, environment examples, and backend dependency file.
2. [x] Implement backend package skeleton with settings, path helpers, and artifact path constants.
3. [x] Implement canonical 35-input feature registry in one backend module, including numeric, categorical, protected, temporal, actionable, and immutable feature lists.
4. [x] Implement Pydantic schemas for `ScoreRequest`, `ScoreResponse`, analytics responses, and common errors.
5. [x] Add unit tests that validate feature-list exclusions, schema constraints, and PRD route contract names.
6. [x] Add the frontend package skeleton and root README placeholder.
7. [x] Implement synthetic data generator with correlated psychometric bases, demographics, cohort month, mild drift, and latent label generation.
8. [x] Implement in-memory data validation helpers and integration tests for default rate, missing values, documented temporal split intent, and protected attribute separation.
9. [x] Persist the raw synthetic dataset and validation summary/report once preprocessing interfaces are ready.
10. [x] Implement local NLP extractor with neutral fallback, pinned local model names, interpretable feature extraction, and raw sentence embedding support.
11. [x] Implement preprocessing fit/transform, train-only text PCA, and explicit split-integrity tests for already-assembled feature datasets.
12. [x] Implement answer parsing and derived feature engineering, and confirm parsed psychometric + behavioral/NLP rows can flow into preprocessing.
13. [x] Implement the behavioral parser and the full raw-request feature assembly path.
14. [x] Implement baseline comparators and the first offline training loop on temporal splits.
15. [x] Implement random forest, XGBoost, and LightGBM training on the same temporal split foundation.
16. [x] Build artifact loading and backend scoring stubs against the fixed inference assembly path.
17. [x] Wire FastAPI startup caching plus `/api/health` and `/api/score` route stubs on top of the artifact loader and scoring service.
18. [x] Add append-only request logging to the `/api/score` stub path.
19. [x] Persist `models/preprocessors/text_pca.pkl` from the offline temporal-train pipeline.
20. [x] Verify runtime request assembly consumes the persisted PCA artifact and only falls back to zero-filled semantics when the artifact is intentionally missing.
21. [x] Add a report-reading analytics service layer so route handlers do not parse report files ad hoc.
22. [x] Add `/api/model-stats` and `/api/baseline-comparison` route stubs backed by saved report files.
23. [x] Add `/api/fairness-report`, `/api/drift-report`, and `/api/global-importance` route stubs backed by the now-persisted report files.
24. [x] Add `/api/score-distribution` backed by a persisted population-percentiles or histogram artifact rather than runtime recomputation.
25. [x] Add `/api/roc-data`, `/api/pr-curve`, `/api/calibration-curve`, and `/api/confusion-matrix` route stubs from the evaluation report structure.
26. [x] Expand analytics endpoint contract tests for both happy-path and missing-artifact responses.
27. [ ] Train TabNet on the documented temporal split with deterministic seeds and smoke coverage.
28. [ ] Train the residual MLP baseline on the documented temporal split with deterministic seeds and smoke coverage.
29. [ ] Train the stacking ensemble from the approved base-model set without crossing train/validation/test boundaries.
30. [ ] Calibrate the ensemble on months 9-10 only and freeze the production-candidate scoring artifact.
31. [ ] Generate the consolidated evaluation bundle, including metrics, curves, confusion matrix data, and score distribution data.
32. [x] Generate SHAP explainability artifacts and dashboard-ready global-importance outputs.
33. [x] Generate the checked-in persisted counterfactual artifact with immutable and protected-feature guards.
34. [x] Generate fairness and PSI drift reports from held-out predictions without using protected fields as model inputs.
35. [ ] Create and validate the production manifest so FastAPI can load one complete serving bundle without fallback mode.

## Detailed Checkpoint Plan

This section expands the next roadmap stretch into smaller delivery checkpoints so future sessions can pick up bounded tasks without re-planning the whole backend and ML path.

| Checkpoint | Theme | Scope | Depends On | Deliverables | Verification / Exit Criteria |
|---|---|---|---|---|---|
| C19 | Persisted text PCA artifact | Save a real `models/preprocessors/text_pca.pkl` from train months `1-8` only and prove it transforms validation/test text features without leakage. | Current preprocessing pipeline, synthetic dataset, local NLP extractor | Saved PCA artifact, updated training commands, integration test for save/load/transform behavior | PCA artifact exists, semantic outputs are finite, runtime feature assembly uses real projections when artifact is supplied |
| C20 | Runtime semantic parity | Remove ambiguity between offline and runtime semantic handling by proving request assembly uses the saved PCA artifact and only zero-fills when the artifact is absent. | C19 | Updated request-assembly behavior, artifact-loader compatibility, explicit fallback coverage | Runtime scoring still works with logistic/classical artifacts, zero-fill remains documented fallback only |
| C21 | Analytics service foundation | Add a backend service layer that loads metrics and report JSON once per request without retraining or hidden recomputation. | Current artifact loader, report path helpers | `backend/app/services/analytics.py` or equivalent, report readers, structured missing-artifact errors | Unit or integration coverage proves report-backed reads and stable error handling |
| C22 | First analytics endpoints | Expose `/api/model-stats` and `/api/baseline-comparison` first because their backing files already exist. | C21, current metrics reports | Route stubs, response mapping, API tests | Endpoints return schema-valid JSON from `metrics.json` and `baseline_metrics.json` |
| C23 | Governance analytics endpoints | Expose `/api/fairness-report`, `/api/drift-report`, and `/api/global-importance` after the persisted fairness, drift, and global-importance artifacts exist. | Fairness, drift, and SHAP artifact jobs | Route stubs, report schemas, missing-artifact behavior | Endpoints return report-backed JSON and fail clearly when reports are absent |
| C24 | Curve and matrix endpoints | Expose `/api/roc-data`, `/api/pr-curve`, `/api/calibration-curve`, and `/api/confusion-matrix` from persisted evaluation outputs. | Evaluation bundle generation | Route stubs, response transformers, curve-bearing report structure | Curve endpoints do not compute model outputs at request time and pass contract tests |
| C25 | Distribution endpoint | Back `/api/score-distribution` with a persisted distribution artifact so percentiles and bands stay consistent between training and serving. | Evaluation bundle generation, percentile logic | Distribution/percentile artifact, route stub, tests | Endpoint returns deterministic histogram/bin payload from saved artifacts |
| C26 | Analytics test hardening | Expand API integration coverage across analytics happy-path, missing-artifact, and schema-regression cases. | C21-C25 | `tests/integration/api/test_analytics_endpoints.py` or split equivalents | Contract tests cover success and failure behavior for the analytics surface |
| C27 | TabNet training foundation | Implement bounded TabNet training on the same temporal split without blending online inference concerns into offline jobs. | Preprocessor, dataset, classical foundation | Training module, script entrypoint, smoke test, saved artifact | Artifact is produced deterministically and metrics merge cleanly into reports |
| C28 | Residual MLP foundation | Add a bounded residual MLP training path with deterministic seeds and shared evaluation/report wiring. | Preprocessor, dataset, classical foundation | Training module, script entrypoint, smoke test, saved artifact | Artifact is produced deterministically and metrics merge cleanly into reports |
| C29 | Ensemble assembly | Train the stacking ensemble from logistic, RF, XGBoost, LightGBM, TabNet, and MLP outputs without split leakage. | C27-C28 plus classical artifacts | Ensemble training module, saved uncalibrated artifact, stack features | Validation stack uses only approved base-model outputs and preserves temporal boundaries |
| C30 | Probability calibration | Calibrate the production candidate using validation months `9-10` only and emit the calibrated serving artifact. | C29 | `calibrated_stacking.pkl`, calibration data in reports, updated registry notes | Calibrated artifact loads cleanly and metrics include Brier/ECE after calibration |
| C31 | Evaluation bundle completion | Persist one richer evaluation bundle containing curves, confusion matrix data, thresholds, distribution data, and any dashboard-needed summaries. | C30 | Expanded `metrics.json` or related report files | Backend analytics routes can serve dashboard data without recomputation |
| C32 | SHAP foundation | Generate the explainability artifact and dashboard-ready global importance outputs from the approved explainable model path. | C30 or approved explainable surrogate path | `shap_explainer.pkl`, `global_importance.json`, optional summary plot | Per-user and global SHAP data are non-trivial and schema-compatible |
| C33 | DICE foundation | Build the DICE artifact and enforce immutable/protected/actionable feature guards for counterfactual generation. | C30, actionable/immutable feature lists | `dice_explainer.pkl`, action-generation helpers, tests | Counterfactual actions avoid protected and immutable features and remain bounded |
| C34 | Fairness and drift bundle | Generate fairness and PSI artifacts from held-out predictions while preserving protected-feature separation from model inputs. | Current logistic/classical artifact bundle, protected audit attributes, test predictions | `fairness_report.json`, `psi_report.json`, status/verdict logic | Reports exist, contain subgroup guardrails, and are readable by analytics routes |
| C35 | Production manifest handoff | Create the first complete manifest-backed serving bundle and make fallback mode optional rather than the default development path. | C19-C34 | `models/registry/production_manifest.json`, manifest validation checks, deployment notes | Backend startup succeeds from one manifest-backed bundle and `/api/health` reflects the promoted artifact set |

## Checkpoint Sequencing Notes

- The repository-integrity checkpoint is now complete: the checked-in SHAP explainer artifact deserializes from restored repo source, the checked-in `dice_explainer.pkl` artifact now validates and serves score actions, the checked-in global-importance artifact matches the active API contract, the default request-log path moved to writable repo-root `runtime/logs/`, and health now distinguishes loaded, missing, and invalid optional artifacts.
- C19 and C20 are complete, and the offline evaluation bundle foundation for score distribution plus ROC/PR/calibration/confusion payloads now exists for the current logistic/classical artifact set.
- C24 through C26 are now complete for the current saved evaluation bundle, and the offline fairness plus PSI artifact foundation is also complete for the current logistic/classical bundle.
- C23 is now complete for the current logistic/classical bundle, so the report-backed governance analytics route surface is in place for fairness, drift, and global importance.
- C27 through C31 are the production-model track and should stay offline-only; none of those jobs should be pulled into FastAPI request handlers.
- The next meaningful backend/product slice after the integrity remediation is now C35 manifest handoff. Per-user SHAP factors, persisted counterfactual actions, fairness, PSI, and the current-contract global-importance report already exist for the current logistic/classical artifact bundle.
- C35 should happen only after the serving bundle can load without relying on the temporary direct-model fallback path.

## Files To Create First

| Priority | File | Purpose |
|---:|---|---|
| 1 | `.gitignore` | Prevent generated data, model binaries, logs, and env files from entering Git |
| 2 | `.env.example` | Document local settings |
| 3 | `backend/requirements.txt` | Pin backend and ML dependencies |
| 4 | `backend/app/core/settings.py` | Central runtime settings |
| 5 | `backend/app/core/paths.py` | Central repository/artifact paths |
| 6 | `backend/ml/preprocessing/feature_registry.py` | Canonical feature lists |
| 7 | `backend/app/schemas/score.py` | Score API contract |
| 8 | `backend/app/schemas/analytics.py` | Analytics API contracts |
| 9 | `tests/unit/ml/test_feature_registry.py` | Guard protected/temporal exclusions |
| 10 | `tests/unit/backend/test_score_schema.py` | Guard API validation |

## Modules Not To Build Early

- Full dashboard charts before analytics JSON reports exist.
- DICE counterfactual runtime integration before a stable calibrated model exists.
- Cloud deployment before local training and serving are reproducible.
- Authentication, user accounts, and persistent borrower profiles unless the PRD is expanded.
- Real lender decision automation; the PRD scope is assessment, scoring, explanations, and demo analytics.
- Complex monitoring infrastructure before baseline logs and health checks exist.
- Manual UI polish before the assessment-to-score contract is stable.

## Dependency Ordering

```text
Docs and contracts
  -> Feature registry
  -> Data generator
  -> Data validation
  -> NLP extractor
  -> Derived features
  -> Preprocessor
  -> Baselines
  -> Classical models
  -> Neural models
  -> Stacking
  -> Calibration
  -> Metrics
  -> SHAP and DICE
  -> Fairness and PSI
  -> Backend APIs
  -> Frontend assessment/results
  -> Frontend dashboard
  -> Deployment
```

## Critical Architectural Risks

| Risk | Why It Matters | Mitigation |
|---|---|---|
| Feature registry drift | Silent schema drift can break training/inference parity | Lock tests to 33 numeric, 2 categorical, and protected/temporal exclusions |
| Protected attribute leakage | Invalidates fairness claims | Tests and explicit exclusion lists |
| Random split leakage | Inflates model quality | Temporal split tests and final metric gates |
| NLP PCA leakage | Test information enters training transformation | Fit PCA only on train embeddings |
| SHAP/DICE serving latency | Score endpoint may become slow | Cache artifacts and cap explanation work |
| Artifact path drift | Backend cannot load trained models | Central path module and manifest |
| Dashboard hardcoding | Analytics lose credibility | Serve all dashboard values from generated reports |
| GPU dependency issues | Neural training may fail locally | Keep classical path working and document GPU setup |
| Synthetic data too easy | Model metrics become unrealistic | Correlated latent labels with noise and baseline comparisons |
| Overbuilt early UI | Frontend churn if schemas change | Lock contracts first |

## Milestones

### M0 - Engineering Foundation

- Docs created.
- Repo scaffold created.
- 35-input feature registry decision recorded.
- Runtime foundation files and settings/path helpers implemented.

### M1 - Data Contract Green

- API and data schemas implemented.
- Feature registry tests pass.
- Synthetic dataset generated and validated.

### M2 - ML Baseline Green

- Local NLP and preprocessing complete.
- Baseline and classical model metrics generated.
- Simulated loan officer comparison exists.

### M2.5 - Runtime Scoring Foundation Green

- Artifact loader supports manifest and temporary direct-model fallback modes.
- Score-mapper and scoring-service stubs can return schema-valid responses from saved artifacts.
- Artifact-loading smoke coverage exists before FastAPI route work begins.

### M2.6 - Backend Route-Stub Foundation Green

- FastAPI app startup caches the runtime artifact bundle.
- `/api/health` and `/api/score` route stubs pass integration coverage.
- The backend can serve schema-valid score responses from saved artifacts before explainability and analytics artifacts are complete.

### M2.7 - Runtime Logging Foundation Green

- `/api/score` appends one JSONL entry per success or failure path.
- Request logs include request ID, latency, status, and runtime model metadata.
- Request logging coverage verifies the log file is created without storing raw request payloads.

### M3 - Production Candidate Green

- Neural models trained.
- Stacking ensemble calibrated.
- Metrics meet minimum targets.

### M4 - Interpretability And Governance Green

- SHAP, DICE, fairness, and PSI reports generated.
- Model registry candidate entry complete.

Current progress toward M4:

- Fairness and PSI report artifacts are already generated for the current logistic/classical artifact bundle.
- A global-importance artifact exists for the current logistic/classical artifact bundle and the checked-in saved payload now matches the active API contract.
- The checked-in `shap_explainer.pkl` and `dice_explainer.pkl` files now both validate from repository source, and `/api/score` now emits persisted per-user SHAP factors plus persisted counterfactual actions from those artifacts. SHAP summary output and future production-model explainability refreshes still remain pending before the full governance backend slice is complete.

### M5 - API Green

- Backend loads artifact bundle.
- All 12 endpoints return schema-valid responses.
- Score endpoint passes edge-case tests.

Current progress toward M5:

- The backend now serves all 12 documented route stubs against the checked-in local bundle, `/api/score` now emits real per-user SHAP explanations plus persisted counterfactual actions, and `/api/health` reports `ok` for the checked-in bundle while still degrading copied or intentionally broken bundles with invalid optional artifacts.
- The remaining API gap is promoting one manifest-backed serving bundle so startup can stop depending on candidate selection or direct-model fallback behavior.

### M6 - Frontend Demo Green

- Assessment flow completes.
- Results page shows score, explanations, actions, and share card.
- Dashboard renders all analytics.

### M7 - Release Green

- Tests pass.
- Deployment docs verified.
- Demo checklist complete.
