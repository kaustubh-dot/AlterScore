# Project Structure

AlterScore is organized around a deployed FastAPI backend, a Vercel-hosted
React frontend, and a checked-in manifest-backed model bundle.

## Top-Level Layout

| Path | Role |
|---|---|
| `.github/workflows/` | CI, backend deployment, and keepalive workflows |
| `backend/` | FastAPI app, scoring service, ML runtime, and offline ML helpers |
| `frontend/` | React/Vite assessment flow, results views, and dashboard |
| `models/` | Production manifest, runtime model artifacts, explainers, and reports |
| `scripts/` | Setup, training, promotion, and validation entry points |
| `tests/` | Unit, integration, API, and pipeline coverage |
| `docs/` | Setup, deployment, API, governance, and runtime references |
| `data/` | Git-kept placeholders for generated local datasets and reports |
| `runtime/` | Ignored local logs and test scratch space |

## Deployment-Critical Files

| File | Why It Matters |
|---|---|
| `Dockerfile` | Hugging Face Spaces backend image |
| `.github/workflows/deploy-hf.yml` | Packages and pushes the backend Space |
| `.github/workflows/ci.yml` | Backend, frontend, and governance checks |
| `frontend/vercel.json` | SPA route rewrites for Vercel |
| `frontend/.env.production` | Public deployed API base URL |
| `models/registry/production_manifest.json` | Runtime artifact contract |

## Active Documentation

| File | Purpose |
|---|---|
| `docs/SETUP.md` | Local setup and validation |
| `docs/DEPLOYMENT.md` | Production deployment and release checks |
| `docs/API_CONTRACTS.md` | API request/response contracts |
| `docs/BACKEND_RUNTIME_ARCHITECTURE.md` | Backend runtime and artifact loading |
| `docs/GOVERNANCE_WORKFLOW.md` | Promotion gates and model governance |
| `docs/MODEL_REGISTRY.md` | Current model artifact inventory |
| `docs/MODEL_SELECTION_DECISIONS.md` | Why the monotonic runtime is preferred |
| `docs/DATA_SCHEMA.md` | Dataset and feature schema reference |
| `docs/ROLLBACK_CHECKLIST.md` | Manifest-based rollback procedure |

Historical process docs, PRD drafts, handoff templates, experiment logs, and
research archives have been removed from the active repository surface.

## Runtime Path

The backend starts at `backend.app.main:app`, loads settings, reads
`models/registry/production_manifest.json`, validates declared checksums, and
serves the manifest-backed artifacts through `/api/score` and analytics routes.

Primary runtime references:

- `backend/app/core/artifact_loader.py`
- `backend/app/services/scoring.py`
- `backend/app/services/analytics.py`
- `backend/ml/inference/feature_assembly.py`
- `models/registry/production_manifest.json`
