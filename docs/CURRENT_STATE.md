# AlterScore Current State

## Snapshot

- Date: 2026-05-13
- Workspace: `C:\Kaustubh\Projects\AlterScore`
- PRD source: `docs/AlterScore_PRD_v2.md`
- Current phase: governance analytics artifact foundation
- Application implementation status: feature registry, runtime foundation helpers, API schemas, the frontend package skeleton, the synthetic data generation/validation foundation, the local NLP extraction foundation, the preprocessing/split-integrity foundation, the answer-parsing/derived-feature foundation, the behavioral/request-assembly foundation, the dataset materialization command, the baseline training loop, the bounded classical training loop for random forest, XGBoost, and LightGBM, the persisted text PCA artifact foundation, the runtime artifact-loading plus scoring-service stubs, the FastAPI app startup with `/api/health`, `/api/score`, `/api/model-stats`, `/api/baseline-comparison`, `/api/score-distribution`, `/api/roc-data`, `/api/pr-curve`, `/api/calibration-curve`, and `/api/confusion-matrix`, append-only request logging on the score path, and the persisted evaluation-artifact foundation for curves, confusion matrices, and score percentiles/distribution are implemented; the remaining governance analytics routes and full production-runtime artifacts are still pending

## What Exists

- Top-level folders already present:
  - `backend/`
  - `data/`
  - `docs/`
  - `frontend/`
  - `models/`
  - `notebooks/`
  - `scripts/`
  - `tests/`
- PRD is available at `docs/AlterScore_PRD_v2.md`.
- Engineering documentation has been scaffolded in `docs/`.
- Mandatory AI workflow rules are available at `docs/AI_WORKFLOW_RULES.md`.
- Repository substructure has been created for backend app code, ML pipeline code, frontend source, experiments, deployment, and tests.
- Canonical feature registry exists at `backend/ml/preprocessing/feature_registry.py`.
- Feature registry unit tests exist at `tests/unit/ml/test_feature_registry.py`.
- Project hygiene and environment files exist: `.gitignore`, `.env.example`, and `backend/requirements.txt`.
- Backend settings and path helpers exist at `backend/app/core/settings.py` and `backend/app/core/paths.py`.
- Backend settings/path unit tests exist at `tests/unit/backend/test_settings.py`.
- Shared backend API schema modules exist at `backend/app/schemas/common.py`, `backend/app/schemas/score.py`, and `backend/app/schemas/analytics.py`.
- Backend schema unit tests exist at `tests/unit/backend/test_score_schema.py` and `tests/unit/backend/test_analytics_schema.py`.
- Frontend package skeleton exists with Vite, React entry files, and base styles under `frontend/`.
- Synthetic data generator and validation helpers exist at `backend/ml/data_generation/generator.py` and `backend/ml/data_generation/validators.py`.
- Dataset materialization and validation-summary helpers exist at `backend/ml/data_generation/artifacts.py`, with command entrypoint `scripts/data/generate_synthetic_dataset.py`.
- Synthetic data integration coverage exists at `tests/integration/pipeline/test_data_generation_validation.py`.
- Local NLP extractor exists at `backend/ml/nlp/extractor.py` with pinned model names, neutral fallback handling, and raw embedding support.
- NLP unit coverage exists at `tests/unit/ml/test_nlp_features.py`.
- Preprocessing pipeline exists at `backend/ml/preprocessing/pipeline.py` with temporal split helpers, train-only text PCA fitting, and sklearn preprocessor fit/transform helpers.
- Preprocessing split-integrity integration coverage exists at `tests/integration/pipeline/test_preprocessing_split_integrity.py`.
- Answer parser exists at `backend/ml/features/answer_parser.py` for the 14 psychometric features from the score request payload.
- Behavioral parser exists at `backend/ml/features/behavioral_parser.py` for canonical telemetry coercion, bounds, and category handling.
- Derived feature engineering exists at `backend/ml/features/derived_features.py`, including row-level merging helpers for already-assembled psychometric, behavioral, and NLP layers.
- Request feature assembly exists at `backend/ml/inference/feature_assembly.py`, which parses answers and behavioral payloads, extracts local NLP features, applies train-fitted text PCA, and returns canonical model-feature rows/dataframes.
- Runtime score mapping exists at `backend/ml/inference/score_mapper.py` for probability-to-score conversion, risk bands, loan eligibility, and percentile fallback behavior.
- Baseline training exists at `backend/ml/training/classical/baselines.py`, with command entrypoint `scripts/training/train_baselines.py`.
- Classical model training exists at `backend/ml/training/classical/train_classical.py`, with command entrypoint `scripts/training/train_classical_models.py`.
- Runtime artifact loading exists at `backend/app/core/artifact_loader.py`, supporting either a production manifest bundle or a direct runtime model path for the current local scoring stub.
- Backend scoring service stubs exist at `backend/app/services/scoring.py`, using the loaded model bundle plus request feature assembly to return schema-valid score responses.
- Backend analytics service foundation now exists at `backend/app/services/analytics.py`, serving report-backed analytics payloads from the loaded runtime bundle.
- FastAPI app startup now exists at `backend/app/main.py`, with artifact loading cached at startup and CORS configured from settings.
- Route stubs now exist at `backend/app/api/v1/routes/health.py`, `backend/app/api/v1/routes/score.py`, and `backend/app/api/v1/routes/analytics.py`.
- Append-only request logging now exists at `backend/app/services/request_logging.py`, writing `/api/score` success and failure entries to `backend/runtime/logs/requests.jsonl` by default without persisting raw request payloads.
- Feature engineering unit coverage exists at `tests/unit/ml/test_answer_parser.py`, `tests/unit/ml/test_behavioral_parser.py`, and `tests/unit/ml/test_derived_features.py`.
- Request-assembly integration coverage exists at `tests/integration/pipeline/test_feature_assembly.py`.
- Dataset-artifact and baseline-training integration coverage exists at `tests/integration/pipeline/test_dataset_artifacts_and_baselines.py`.
- Classical training integration coverage exists at `tests/integration/pipeline/test_classical_training.py`.
- Artifact-loading and scoring-stub integration coverage exists at `tests/integration/pipeline/test_artifact_loading.py`.
- Persisted text PCA artifact integration coverage now exists at `tests/integration/pipeline/test_text_pca_artifact.py`.
- API integration coverage now exists at `tests/integration/api/test_health_endpoint.py`, `tests/integration/api/test_score_endpoint.py`, and `tests/integration/api/test_analytics_endpoints.py`.
- Score-mapper unit coverage exists at `tests/unit/ml/test_score_mapper.py`.
- A reusable valid score-request smoke fixture now exists at `tests/fixtures/score_request_valid.json`.
- Persisted synthetic dataset now exists at `data/raw/synthetic_dataset.csv`.
- Persisted validation summary now exists at `data/validation/validation_summary.json`.
- Refreshed baseline artifacts now exist at `models/preprocessors/preprocessor.pkl`, `models/preprocessors/text_pca.pkl`, `models/artifacts/logistic_best.pkl`, `models/reports/baseline_metrics.json`, and `models/reports/metrics.json`.
- Saved classical model artifacts now exist at `models/artifacts/rf_best.pkl`, `models/artifacts/xgb_best.pkl`, and `models/artifacts/lgbm_best.pkl`.
- `models/reports/metrics.json` now preserves the baseline section, includes validation/test rows for `random_forest`, `xgboost`, and `lightgbm`, and stores offline `evaluation_details` for validation/test ROC, PR, calibration, and confusion payloads.
- `models/reports/population_percentiles.json` now exists with a real score histogram plus percentile lookup for the scored synthetic population, and it carries model-specific tables for the current logistic/classical artifacts.
- Offline training now reconstructs deterministic runtime-compatible surrogate Q27 text from the persisted synthetic dataset when raw text is unavailable, then fits `text_pca.pkl` on train months `1-8` only and saves evaluation artifacts from the same offline feature path.
- Runtime artifact loading now resolves the active model's percentile table from a multi-model `population_percentiles.json` payload, so direct logistic fallback, candidate classical loading, and later ensemble loading can all reuse the same artifact format.
- Root project placeholder README exists at `README.md`.
- Frontend scaffold verification exists at `tests/unit/frontend/test_frontend_skeleton.py`.

## What Does Not Exist Yet

- No borrower assessment pages, results flow, dashboard workflow, or frontend tests beyond the package skeleton smoke test.
- No neural, stacking, calibration, SHAP, DICE, fairness, or PSI jobs yet.
- Report-backed analytics now cover `/api/model-stats`, `/api/baseline-comparison`, `/api/score-distribution`, `/api/roc-data`, `/api/pr-curve`, `/api/calibration-curve`, and `/api/confusion-matrix`. Fairness, drift, and global-importance analytics remain pending because their offline report artifacts do not exist yet. Interactive frontend tests beyond the package skeleton smoke test and broader ML validation beyond the current feature, preprocessing, training, artifact-loading, evaluation-artifact, and API foundation coverage are also still pending.
- No Docker runtime files yet.
- No SHAP explainer or DICE explainer exists yet, so the current scoring stub still returns empty explanation/counterfactual lists; semantic features now use the persisted `text_pca.pkl` when available and only fall back to zero-filled projections when the PCA artifact is intentionally missing.

## PRD-Derived Product Summary

AlterScore scores alternative creditworthiness through a 27-question assessment plus behavioral telemetry and a local NLP analysis of one open-text response. The system must generate a calibrated 300-850 credit score, risk band, percentile, SHAP explanation, DICE counterfactual improvement actions, loan eligibility, and dashboard analytics for model quality, fairness, and drift.

## Feature Count Decision

The implementation will use the explicit named model inputs from the PRD as the source of truth:

- 33 numeric model features
- 2 categorical model features
- 35 total model inputs
- 4 protected audit-only attributes

The earlier PRD narrative referenced 39 features, but the project will not invent four unnamed features. Future implementation must preserve the 35 named inputs documented in `docs/DATA_SCHEMA.md`.

## Current Architectural Decisions

- Use FastAPI backend.
- Use React frontend.
- Use local NLP only.
- Use offline ML training separated from runtime inference.
- Use calibrated stacking ensemble as production scoring model.
- Use SHAP and DICE-ML for explanations.
- Use PSI and fairness reports for dashboard analytics.
- Use temporal cohort split for final validation.

## Immediate Next Step

Continue the implementation foundation in this order:

1. Generate the offline fairness, drift, and global-importance report artifacts so the remaining governance analytics routes have real saved payloads.
2. Add `/api/fairness-report`, `/api/drift-report`, and `/api/global-importance` once those offline reports exist.
3. Keep the refreshed logistic, classical, preprocessor, `text_pca.pkl`, `metrics.json`, `baseline_metrics.json`, and `population_percentiles.json` artifacts as the local offline foundation while neural and ensemble training are still pending.

## Session Update Protocol

Every future session must follow `docs/AI_WORKFLOW_RULES.md` and should update this file with:

- Date and branch.
- What changed.
- Files edited.
- Tests run.
- Open blockers.
- Exact recommended next action.
