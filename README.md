---
title: AlterScore Backend
emoji: 📊
colorFrom: green
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---

# AlterScore

AlterScore is a governed behavioral credit scoring platform for unbanked and
thin-file borrowers. It combines psychometric questionnaires, behavioral
telemetry, and NLP-derived signals, then evaluates candidates through strict
governance requirements including monotonicity, pairwise counterfactual
stability, fairness review, calibration review, drift analysis, and promotion
gating.

## Current Runtime

The checked-in production runtime is now a manifest-backed **monotonic
XGBoost** scorer:

- Runtime model: `xgboost_monotonic`
- Runtime type: `classical_monotonic`
- Manifest: `models/registry/production_manifest.json`
- Manifest version: `xgboost_monotonic_v1`
- Checked-in test AUC: `0.8040`
- Checked-in Brier score: `0.1514`
- Checked-in ECE: `0.0284`
- Checked-in drift verdict: `stable`

The earlier calibrated stacking ensemble remains in the repository as a
validated benchmark and rollback/reference bundle, but it is no longer the
default manifest runtime. The governed full-scale comparison that led to the
promotion recorded stronger `xgboost_monotonic` results (`0.8090` AUC,
`0.1496` Brier, `0.0207` ECE), while the current checked-in fairness report
still flags `gender=non_binary` for review. Treat fairness hardening and report
reconciliation as pre-pilot work, not as optional polish.

TabNet remains in the repository as a research benchmark and governance case
study.

## Quickstart

Run from the repository root.

```powershell
# 1. Create a Python 3.12 environment for backend work
py -3.12 -m venv backend\.venv-cleanup

# 2. Install backend dependencies
backend\.venv-cleanup\Scripts\python.exe -m pip install -r backend\requirements.txt

# 3. Optional: install backend dev/test dependencies
backend\.venv-cleanup\Scripts\python.exe -m pip install -r backend\requirements-dev.txt

# 4. Start the backend
backend\.venv-cleanup\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

In a second terminal:

```powershell
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

Useful endpoints:

- Backend health: `http://127.0.0.1:8000/api/health`
- Frontend app: `http://127.0.0.1:5173`
- Analytics endpoints: `http://127.0.0.1:8000/api/...`

## Validation Commands

```powershell
# Focused backend and pipeline coverage
backend\.venv-cleanup\Scripts\python.exe -m pytest tests\unit\ml\ -v

# Runtime/API smoke coverage
backend\.venv-cleanup\Scripts\python.exe -m pytest tests\integration\api\test_checked_in_runtime_bundle_smoke.py -v

# Governed production-track comparison
backend\.venv-cleanup\Scripts\python.exe scripts\train_monotonic_tree_candidates.py --row-count 10000

# Fairness hardening review for the leading XGBoost candidate
backend\.venv-cleanup\Scripts\python.exe scripts\fairness_harden_xgboost_candidate.py --row-count 10000
```

## Repository Guide

| Directory | Purpose |
|---|---|
| `backend/` | FastAPI backend, inference path, offline ML, governance helpers |
| `frontend/` | Borrower UI and evaluator-facing frontend |
| `models/` | Checked-in production runtime bundle, manifest, and core reports |
| `scripts/` | Setup, training, evaluation, governance, and maintenance entrypoints |
| `tests/` | Unit and integration coverage |
| `docs/` | Architecture, setup, governance, decisions, and project memory |
| `runtime/` | Local generated outputs split into governed reports and research archive |
| `archive/` | Archived experiment notes and repository-level archive guidance |
| `data/` | Generated datasets and validation artifacts |

## Key Documentation

| Document | Purpose |
|---|---|
| [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) | High-level repository organization and active vs archived areas |
| [docs/REPO_AUDIT_2026-05-25.md](docs/REPO_AUDIT_2026-05-25.md) | Latest repository hygiene/runtime alignment audit |
| [docs/GOVERNANCE_WORKFLOW.md](docs/GOVERNANCE_WORKFLOW.md) | Promotion gates, audit flow, and governance operating model |
| [docs/MODEL_SELECTION_DECISIONS.md](docs/MODEL_SELECTION_DECISIONS.md) | Why monotonic XGBoost became the leading production path |
| [docs/governance/GOVERNED_PRODUCTION_ARCHITECTURE.md](docs/governance/GOVERNED_PRODUCTION_ARCHITECTURE.md) | Current governed production architecture |
| [docs/governance/MONOTONIC_TREE_GOVERNED_COMPARISON.md](docs/governance/MONOTONIC_TREE_GOVERNED_COMPARISON.md) | Full constrained-tree governed comparison |
| [docs/governance/XGBOOST_FAIRNESS_HARDENING_PROMOTION_REVIEW.md](docs/governance/XGBOOST_FAIRNESS_HARDENING_PROMOTION_REVIEW.md) | Final fairness hardening and promotion review |
| [docs/SETUP.md](docs/SETUP.md) | Setup and onboarding |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | Deployment expectations and runtime environment variables |
| [docs/BACKEND_RUNTIME_ARCHITECTURE.md](docs/BACKEND_RUNTIME_ARCHITECTURE.md) | Checked-in runtime bundle behavior |
| [docs/API_CONTRACTS.md](docs/API_CONTRACTS.md) | Request and response contracts |

## Reproducibility Notes

- The checked-in production bundle still loads through the current backend
  runtime path.
- Governed production-track evaluation is reproducible through the monotonic
  tree and fairness-hardening scripts.
- Research-stage TabNet audit outputs are preserved in `runtime/research_archive/`
  and in `docs/research_archive/`.
- Frontend dependencies are not committed; use `npm install` from a clean clone.

## Workflow

Follow [docs/AI_WORKFLOW_RULES.md](docs/AI_WORKFLOW_RULES.md) and
[docs/ENGINEERING_CONTEXT.md](docs/ENGINEERING_CONTEXT.md) before making
changes. They define startup checks, documentation obligations, testing
expectations, and repository hygiene rules for this codebase.
