# AlterScore Current State

## Snapshot

- Date: 2026-05-13
- Workspace: `C:\Kaustubh\Projects\AlterScore`
- PRD source: `docs/AlterScore_PRD_v2.md`
- Current phase: frontend package foundation
- Application implementation status: feature registry, runtime foundation helpers, API schemas, and the frontend package skeleton are implemented; app runtime is still in scaffold stage

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
- Root project placeholder README exists at `README.md`.
- Frontend scaffold verification exists at `tests/unit/frontend/test_frontend_skeleton.py`.

## What Does Not Exist Yet

- No FastAPI application code.
- No borrower assessment pages, results flow, dashboard workflow, or frontend tests beyond the package skeleton smoke test.
- No data generator implementation.
- No model training scripts.
- No generated dataset.
- No trained artifacts.
- No FastAPI route or API integration tests, no interactive frontend tests beyond the package skeleton smoke test, and no broader ML validation tests beyond feature and schema unit tests.
- No FastAPI app entrypoint, route modules, or Docker runtime files yet.

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

1. Implement synthetic data generator and validation tests.
2. Implement local NLP feature extractor.
3. Implement preprocessing pipeline.
4. Implement backend route stubs only after contracts remain stable.
5. Build frontend assessment pages only after backend scoring flow is wired.

## Session Update Protocol

Every future session must follow `docs/AI_WORKFLOW_RULES.md` and should update this file with:

- Date and branch.
- What changed.
- Files edited.
- Tests run.
- Open blockers.
- Exact recommended next action.
