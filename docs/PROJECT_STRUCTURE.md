# Project structure

AlterScore is organized around a public deterministic v2 service and a Vercel
React frontend. Retired research payloads are excluded from the production
repository.

## Active layout

| Path | Role |
| --- | --- |
| `backend/app/api/v2/` | Anonymous form, score, verification, liveness, and readiness routes |
| `backend/app/instrument/` | Canonical server-owned objective and judgment instrument |
| `backend/app/branching/` | Deterministic financial-state transitions and replays |
| `backend/app/unified_scoring/` | Frozen score composition and explanation construction |
| `frontend/` | Assessment, processing, explainable results, dashboard, and static Research Lab |
| `tests/` | Public v2, instrument, branching, unified-scoring, and Phase 7 coverage |
| `docs/` | Active contract, architecture, setup, deployment, rollback, and governance docs |

## Retired research boundary

The former ML source tree, serialized artifacts, explainers, training scripts,
client question bank, Admin surface, and legacy tests are intentionally absent
from the production branch. They remain recoverable through Git history and
the pre-production backup branch, but are never imported, packaged, or served.

## Deployment-critical files

| File | Role |
| --- | --- |
| `Dockerfile` | Allow-listed v2 serving image |
| `.dockerignore` | Build-context defense in depth |
| `backend/requirements.txt` | Human-reviewed direct serving dependencies |
| `backend/requirements.lock` | Hash-locked Linux production serving environment |
| `frontend/.env.production` | Public frontend API base URL |
| `.github/workflows/deploy-hf.yml` | Trusted CI-gated paired-release authority with verified manifest retention |

The production entrypoint is `backend.app.main:app`. It does not load a model
manifest, serialized artifact, report, or legacy request logger.
