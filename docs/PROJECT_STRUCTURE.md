# Project structure

AlterScore is organized around a public deterministic v2 service, a Vercel
React frontend, and a clearly separated offline research archive.

## Active layout

| Path | Role |
| --- | --- |
| `backend/app/api/v2/` | Anonymous form, score, verification, liveness, and readiness routes |
| `backend/app/instrument/` | Canonical server-owned objective and judgment instrument |
| `backend/app/branching/` | Deterministic financial-state transitions and replays |
| `backend/app/unified_scoring/` | Frozen score composition and explanation construction |
| `frontend/` | Assessment, processing, explainable results, dashboard, and static Research Lab |
| `tests/` | Public v2, instrument, branching, unified-scoring, and Phase 7 coverage |
| `docs/` | Active contract, architecture, setup, deployment, rollback, and methodology docs |

## Research archive

`research/legacy_synthetic_model/` contains the former ML source tree, model
artifacts, explainers, parsers, training/validation scripts, client question
bank, Admin surface, and legacy tests. It is not imported by `backend/app`,
copied by the production Dockerfile, or reachable through public research
routes.

The archive's labels and fairness reports are synthetic. Archived AUC values
measure recovery of generated data. The archived model does not score public
assessments.

## Deployment-critical files

| File | Role |
| --- | --- |
| `Dockerfile` | Allow-listed v2 serving image |
| `.dockerignore` | Build-context defense in depth |
| `backend/requirements.txt` | Serving-only dependencies |
| `frontend/.env.production` | Public frontend API base URL |
| `.github/workflows/deploy-hf.yml` | Backend package delivery; release hardening is tracked separately |

The production entrypoint is `backend.app.main:app`. It does not load a model
manifest, serialized artifact, report, or legacy request logger.
