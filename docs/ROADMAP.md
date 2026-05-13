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

## Exact First 10 Implementation Steps

1. Create `.gitignore`, environment examples, backend dependency file, frontend package skeleton, and root README placeholder.
2. Implement backend package skeleton with settings, path helpers, and artifact path constants.
3. Implement canonical 35-input feature registry in one backend module, including numeric, categorical, protected, temporal, actionable, and immutable feature lists.
4. Implement Pydantic schemas for `ScoreRequest`, `ScoreResponse`, analytics responses, and common errors.
5. Add unit tests that validate feature-list exclusions, schema constraints, and PRD route contract names.
6. Implement synthetic data generator with correlated psychometric bases, demographics, cohort month, mild drift, and latent label generation.
7. Implement data validation job and tests for default rate, missing values, temporal split, feature ranges, and protected attribute separation.
8. Implement local NLP extractor with neutral fallback, VADER sentiment, spaCy agency/problem-solving features, and raw sentence embedding support.
9. Implement derived feature engineering and answer parser with tests using known answer payloads.
10. Implement preprocessing fit/transform pipeline, save `preprocessor.pkl` and `text_pca.pkl`, and add train/validation/test split integrity tests.

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

### M1 - Data Contract Green

- API and data schemas implemented.
- Feature registry tests pass.
- Synthetic dataset generated and validated.

### M2 - ML Baseline Green

- Local NLP and preprocessing complete.
- Baseline and classical model metrics generated.
- Simulated loan officer comparison exists.

### M3 - Production Candidate Green

- Neural models trained.
- Stacking ensemble calibrated.
- Metrics meet minimum targets.

### M4 - Interpretability And Governance Green

- SHAP, DICE, fairness, and PSI reports generated.
- Model registry candidate entry complete.

### M5 - API Green

- Backend loads artifact bundle.
- All 12 endpoints return schema-valid responses.
- Score endpoint passes edge-case tests.

### M6 - Frontend Demo Green

- Assessment flow completes.
- Results page shows score, explanations, actions, and share card.
- Dashboard renders all analytics.

### M7 - Release Green

- Tests pass.
- Deployment docs verified.
- Demo checklist complete.
