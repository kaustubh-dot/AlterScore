# AlterScore Current State

## Snapshot

- Date: 2026-05-13
- Workspace: `C:\Kaustubh\Projects\AlterScore`
- PRD source: `docs/AlterScore_PRD_v2.md`
- Current phase: engineering organization and project scaffolding
- Application implementation status: not started

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

## What Does Not Exist Yet

- No FastAPI application code.
- No React application code.
- No data generator implementation.
- No feature registry implementation.
- No model training scripts.
- No generated dataset.
- No trained artifacts.
- No API tests, frontend tests, or ML validation tests.
- No deployment runtime files beyond scaffold folders.

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

Create the implementation foundation in this order:

1. Feature registry and schema constants.
2. Backend and ML package skeletons.
3. Synthetic data generator and validation tests.
4. Local NLP feature extractor.
5. Preprocessing pipeline.

## Session Update Protocol

Every future session must follow `docs/AI_WORKFLOW_RULES.md` and should update this file with:

- Date and branch.
- What changed.
- Files edited.
- Tests run.
- Open blockers.
- Exact recommended next action.
