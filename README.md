# AlterScore

AlterScore is an alternative credit scoring platform for unbanked and thin-file
borrowers. The project combines psychometric assessment answers, behavioral
telemetry, and local NLP signals to generate credit scores, explanations,
counterfactual improvement actions, and evaluator analytics.

## Status

Backend tracks A–D are complete. The checked-in manifest-backed runtime bundle
includes a logistic regression model, preprocessor, text PCA, SHAP and DICE
explainers, and all governance reports (fairness, PSI, global importance,
metrics, population percentiles). Offline training pipelines for classical
models (RF, XGBoost, LightGBM), neural models (TabNet, MLP), and a calibrated
stacking ensemble are implemented and tested. The scoring API (`/api/score`)
returns real per-user SHAP factors, counterfactual actions, and loan eligibility
from the manifest-backed bundle. The frontend borrower experience (Track E) is
the next milestone.

## Repository Guide

- `docs/` contains the project memory, workflow rules, roadmap, and contracts.
- `backend/` contains API, ML, and runtime foundation code.
- `frontend/` contains the React/Vite package skeleton for future UI work.
- `tests/` contains contract and scaffold verification.

## Local Development

Backend and frontend are intended to run independently during development.
Current commands and environment variables are documented in
`docs/DEPLOYMENT.md`.

**Note:** Python `>=3.10` is required. The checked-in artifacts are serialized
with `scikit-learn >=1.8.0`. See `backend/requirements.txt` for pinned
dependency versions.

## Workflow

Follow `docs/AI_WORKFLOW_RULES.md` before making changes. It defines the
required startup checks, testing expectations, and documentation update rules
for this repository.
