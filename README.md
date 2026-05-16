# AlterScore

AlterScore is an alternative credit scoring platform for unbanked and thin-file
borrowers. The project combines psychometric assessment answers, behavioral
telemetry, and local NLP signals to generate credit scores, explanations,
counterfactual improvement actions, and evaluator analytics.

## Status

Backend Tracks A–D+ are complete. The checked-in manifest-backed runtime bundle
serves a **calibrated stacking ensemble** (6 base models: Logistic, RF, XGBoost,
LightGBM, TabNet, MLP) with a calibrated meta-learner. The bundle includes the
preprocessor, text PCA, SHAP and DICE explainers, and all governance reports
(fairness, PSI, global importance, metrics, population percentiles). The scoring
API (`/api/score`) returns real per-user SHAP factors, counterfactual actions,
and loan eligibility through the full ensemble inference path. The frontend
borrower experience (Track E) is the next milestone.

## Quick Start

```powershell
# 1. Install backend dependencies
cd backend
python -m pip install -r requirements.txt

# 2. Start backend (loads manifest-backed bundle automatically)
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# 3. Verify backend health
curl http://localhost:8000/api/health

# 4. Install frontend dependencies
cd ../frontend
npm install

# 5. Start frontend dev server
npm run dev -- --host 127.0.0.1 --port 5173

# 6. Run tests
cd ..
python -m pytest tests/ -v
```

## Repository Guide

| Directory | Purpose |
|---|---|
| `docs/` | Project memory, contracts, workflow rules, and roadmap |
| `backend/` | FastAPI backend, ML pipelines, and runtime inference |
| `frontend/` | React/Vite package scaffold for borrower and dashboard UI |
| `tests/` | Unit, integration, and fixture files (145 tests) |
| `models/` | Checked-in runtime artifacts and production manifest |
| `scripts/` | CLI entrypoints for offline training pipelines |
| `data/` | Generated datasets (gitignored except `.gitkeep`) |

## Key Documentation

| Document | When To Read It |
|---|---|
| [BACKEND_RUNTIME_ARCHITECTURE.md](docs/BACKEND_RUNTIME_ARCHITECTURE.md) | **Read first** — explains the ensemble serving architecture and what not to break |
| [FRONTEND_INTEGRATION_GUIDE.md](docs/FRONTEND_INTEGRATION_GUIDE.md) | Before writing any frontend code — covers all API contracts, telemetry, rendering guidance |
| [API_CONTRACTS.md](docs/API_CONTRACTS.md) | Reference for all request/response schemas |
| [ROADMAP.md](docs/ROADMAP.md) | Track status and implementation order |
| [TODO.md](docs/TODO.md) | Detailed task queue |
| [CURRENT_STATE.md](docs/CURRENT_STATE.md) | What exists, what doesn't, architectural decisions |
| [ENGINEERING_CONTEXT.md](docs/ENGINEERING_CONTEXT.md) | Deep technical context and constraints |
| [TESTING_STRATEGY.md](docs/TESTING_STRATEGY.md) | Test layout, requirements, and acceptance gates |
| [DEPLOYMENT.md](docs/DEPLOYMENT.md) | Environment variables, Docker plan, rollback |
| [DECISIONS.md](docs/DECISIONS.md) | Architecture decision records |
| [AI_WORKFLOW_RULES.md](docs/AI_WORKFLOW_RULES.md) | Required reading before AI-assisted sessions |

## Environment Requirements

- **Python** `>=3.10` — tested on 3.14.3
- **scikit-learn** `>=1.8.0` — checked-in artifacts require this version
- **Node.js** `>=18` — frontend build
- See `backend/requirements.txt` and `frontend/package.json` for pinned versions

## Branch Strategy

- `main` — stable, merged only after full test suite passes
- `feature/ensemble-serving-runtime` — current development branch (backend complete, frontend next)
- Frontend work should branch from `main` after merge

## Test Suite

```powershell
# Full suite (145 tests, ~12 minutes)
python -m pytest tests/ -v

# Fast feedback (unit + API smoke, ~2 minutes)
python -m pytest tests/unit/ tests/integration/api/ -v

# Checked-in bundle smoke only (~20 seconds)
python -m pytest tests/integration/api/test_checked_in_runtime_bundle_smoke.py -v
```

## Workflow

Follow `docs/AI_WORKFLOW_RULES.md` before making changes. It defines the
required startup checks, testing expectations, and documentation update rules
for this repository.
