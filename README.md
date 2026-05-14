# AlterScore

AlterScore is an alternative credit scoring platform for unbanked and thin-file
borrowers. The project combines psychometric assessment answers, behavioral
telemetry, and local NLP signals to generate credit scores, explanations,
counterfactual improvement actions, and evaluator analytics.

## Status

The repository is still in foundation mode, but the checked-in runtime-bundle
integrity pass is now in place. Backend feature contracts, runtime helpers, API
schemas, offline baseline/classical training, runtime artifact loading, FastAPI
health/score route stubs, and the current analytics route surface all work
against the saved local bundle. The restored SHAP compatibility module now lets
the checked-in explainer deserialize, the saved global-importance artifact now
matches the active API contract, score-request logging now defaults to the
repo-root `runtime/logs/requests.jsonl` path, and `/api/score` now returns
real per-user SHAP factors plus persisted counterfactual actions from the
checked-in `models/explainers/dice_explainer.pkl` artifact. The repository also
now tracks a small local runtime bundle so smoke tests can validate the real
serving assets directly. Broader product flows are still pending, especially
manifest-backed serving and the full production ensemble path.

## Repository Guide

- `docs/` contains the project memory, workflow rules, roadmap, and contracts.
- `backend/` contains API, ML, and runtime foundation code.
- `frontend/` contains the React/Vite package skeleton for future UI work.
- `tests/` contains contract and scaffold verification.

## Local Development

Backend and frontend are intended to run independently during development.
Current commands and environment variables are documented in
`docs/DEPLOYMENT.md`.

## Workflow

Follow `docs/AI_WORKFLOW_RULES.md` before making changes. It defines the
required startup checks, testing expectations, and documentation update rules
for this repository.
