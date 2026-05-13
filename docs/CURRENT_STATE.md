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

## Important PRD Consistency Note

The PRD states "39 model features" using four layers:

- 18 psychometric
- 9 behavioral telemetry
- 5 NLP
- 7 derived

The explicit `NUMERIC_FEATURES` and `CATEGORICAL_FEATURES` list in the PRD names:

- 33 numeric model features
- 2 categorical model features
- 4 protected audit-only attributes

Before implementation, the feature registry must reconcile this difference without inventing unsupported columns. Until resolved, preserve both facts:

- Product target: 39 feature concept from the PRD narrative.
- Implementation registry: explicit named model inputs from the PRD code block.

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

Every future session should update this file with:

- Date and branch.
- What changed.
- Files edited.
- Tests run.
- Open blockers.
- Exact recommended next action.

