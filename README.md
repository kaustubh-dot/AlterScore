# AlterScore

AlterScore is an alternative credit scoring platform for unbanked and thin-file
borrowers. The project combines psychometric assessment answers, behavioral
telemetry, and local NLP signals to generate credit scores, explanations,
counterfactual improvement actions, and evaluator analytics.

## Status

The repository is in foundation mode. Backend feature contracts, runtime
helpers, API schemas, offline baseline/classical training, runtime artifact
loading, FastAPI health/score route stubs, and append-only score-request
logging exist. Analytics routes, explainability artifacts, and broader
application flows are still pending.

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
