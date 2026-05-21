# AlterScore

AlterScore is an alternative credit scoring platform for unbanked and thin-file
borrowers. It combines psychometric answers, behavioral telemetry, and local
NLP signals to produce credit scores, explanations, counterfactual actions, and
analytics-ready reporting.

## Current Working State

- Backend runtime is implemented and manifest-backed.
- The checked-in production bundle serves a calibrated stacking ensemble with
  six base models plus saved preprocessors, explainers, and reports.
- The borrower frontend is implemented in React/Vite.
- The evaluator dashboard exists as a shell, but full analytics-panel wiring is
  still pending.
- This cleanup pass does not modify core scoring or model logic.

## Quickstart

Run from the repository root.

```powershell
# 1. Verify the supported local toolchain
& 'C:\Users\Kaustubh\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scripts\setup\check_environment.py

# 2. Create a fresh Python 3.12 environment
& 'C:\Users\Kaustubh\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m venv backend\.venv-cleanup

# 3. Install backend dependencies
backend\.venv-cleanup\Scripts\python.exe -m pip install -r backend\requirements.txt

# 4. Optional: install backend test dependencies
backend\.venv-cleanup\Scripts\python.exe -m pip install -r backend\requirements-dev.txt

# 5. Start the backend from the repo root
backend\.venv-cleanup\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

In a second terminal:

```powershell
cd frontend
& 'C:\Program Files\nodejs\npm.cmd' install
& 'C:\Program Files\nodejs\npm.cmd' run dev -- --host 127.0.0.1 --port 5173
```

Then verify:

- Backend health: `http://127.0.0.1:8000/api/health`
- Frontend app: `http://127.0.0.1:5173`

## Environment Requirements

- Python `3.12.x`
- Node.js `>=18 <25`
- npm `>=9 <12`
- scikit-learn `>=1.8,<1.9`

Python `3.10` is the syntax floor for the codebase, but the recommended local
setup target is Python `3.12.x`. Python `3.14.x` is not part of the supported
local workflow for this repository today.

## Repository Guide

| Directory | Purpose |
|---|---|
| `backend/` | FastAPI backend, runtime loading, inference, and offline ML modules |
| `frontend/` | React/Vite borrower UI and evaluator dashboard shell |
| `models/` | Checked-in manifest-backed runtime artifacts and reports |
| `scripts/` | Setup, data, training, and maintenance entrypoints |
| `tests/` | Unit and integration coverage |
| `docs/` | Setup, architecture, contracts, roadmap, and project memory |
| `data/` | Generated datasets and validation outputs |

## Key Documentation

| Document | Purpose |
|---|---|
| [docs/SETUP.md](docs/SETUP.md) | Setup, onboarding, troubleshooting, and known current issues |
| [backend/README.md](backend/README.md) | Backend startup, runtime expectations, and health checks |
| [frontend/README.md](frontend/README.md) | Frontend startup and API connectivity notes |
| [docs/BACKEND_RUNTIME_ARCHITECTURE.md](docs/BACKEND_RUNTIME_ARCHITECTURE.md) | Runtime bundle and scoring-path architecture |
| [docs/FRONTEND_INTEGRATION_GUIDE.md](docs/FRONTEND_INTEGRATION_GUIDE.md) | Score flow and analytics integration guidance |
| [docs/API_CONTRACTS.md](docs/API_CONTRACTS.md) | Request and response contracts |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Deployment expectations and runtime environment variables |
| [docs/CURRENT_STATE.md](docs/CURRENT_STATE.md) | Snapshot of what is working right now |
| [docs/TESTING_STRATEGY.md](docs/TESTING_STRATEGY.md) | Test layout, expectations, and milestone gates |

## Known Current Issues

- Scoring logic is still under audit and should not be treated as finalized.
- Model behavior and score calibration remain under investigation for the next
  debugging phase.
- The evaluator dashboard shell is present, but full panel wiring is incomplete.
- Frontend coverage is still lighter than backend and pipeline coverage.
- The WebGL/R3F frontend build may emit a non-critical bundle-size warning.
- Fresh `npm install` currently reports 5 frontend dependency vulnerabilities in
  transitive packages; `npm audit` could not be completed in this environment
  without registry access.

## Validation Commands

```powershell
# Backend tests
backend\.venv-cleanup\Scripts\python.exe -m pytest tests\ -v

# Focused API smoke coverage
backend\.venv-cleanup\Scripts\python.exe -m pytest tests\integration\api\test_checked_in_runtime_bundle_smoke.py -v

# Frontend production build
cd frontend
& 'C:\Program Files\nodejs\npm.cmd' run build
```

## Workflow

Follow [docs/AI_WORKFLOW_RULES.md](docs/AI_WORKFLOW_RULES.md) before making
changes. It defines the repository's expectations for startup checks,
documentation updates, testing, and git hygiene.
