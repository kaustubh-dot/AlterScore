# AlterScore Setup And Onboarding

This document is the single source of truth for local setup, quickstart,
troubleshooting, and contributor onboarding.

## Current Working State

- Backend runtime is manifest-backed and loads the checked-in monotonic
  `XGBoost` production bundle.
- Borrower frontend is implemented and can submit to `/api/score`.
- Evaluator dashboard analytics panels, confusion-matrix view, independent panel states, and async loaders are fully implemented and verified.
- The earlier calibrated stacking ensemble remains available as a benchmark and
  rollback/reference artifact, but it is not the default manifest runtime.

## Environment Requirements

| Tool | Required | Notes |
|---|---|---|
| Python | `3.12.x` | Recommended local interpreter family |
| Node.js | `>=18 <25` | Frontend development/build |
| npm | `>=9 <12` | Use `npm.cmd` on Windows PowerShell if needed |
| scikit-learn | `>=1.8,<1.9` | Required by checked-in artifacts |

Not recommended for this repo's normal local setup:

- Python `3.14.x`
- ad hoc backend startup from inside `backend/` using `app.main:app`

## Quickstart

Run from the repository root unless a step says otherwise.

```powershell
# 1. Create a Python 3.12 virtual environment at the repository root
python -m venv venv

# 2. Activate the virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# macOS/Linux (Bash):
source venv/bin/activate

# 3. Upgrade pip and install core dependencies
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt

# 4. Optional: install backend test dependencies
python -m pip install -r backend/requirements-dev.txt

# 5. Start the backend from the repo root
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

In a second terminal:

```powershell
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

## Validation Checklist

Backend:

1. `GET http://127.0.0.1:8000/api/health` returns 200.
2. `manifest_backed` is `true`.
3. `model_loaded` is `true`.
4. `missing_artifacts` and `invalid_artifacts` are empty for the checked-in bundle.

Frontend:

1. `http://127.0.0.1:5173` loads.
2. The app can reach `VITE_API_BASE_URL`.
3. The assessment flow can submit to `/api/score`.

## Dependency Files

- Backend runtime: `backend/requirements.txt`
- Backend test extras: `backend/requirements-dev.txt`
- Frontend dependencies: `frontend/package.json`
- Frontend lockfile: `frontend/package-lock.json`
- Suggested Python pin for version managers: `.python-version`
- Local environment example: `.env.example`

## Contributor Onboarding Notes

- Start from `README.md`, then read this document.
- For backend runtime work, read `docs/BACKEND_RUNTIME_ARCHITECTURE.md`.
- For governed production-track work, read `docs/governance/GOVERNED_PRODUCTION_ARCHITECTURE.md`.
- For frontend work, read `docs/FRONTEND_INTEGRATION_GUIDE.md`.
- For contract-sensitive changes, read `docs/API_CONTRACTS.md`.
- Do not change scoring logic, serialized model artifacts, or manifest contents
  during cleanup-only work.

## Troubleshooting

- If PowerShell blocks `npm`, use `npm.cmd`.
- If you start the backend from inside `backend/`, imports will be inconsistent
  with the current package layout. Start from the repository root with
  `backend.app.main:app` instead.
- If a fresh backend install on Windows fails under Python `3.14.x`, switch to
  Python `3.12.x`.
- If `sentence-transformers` cannot download a model, the backend falls back to
  deterministic hashed embeddings.
- If `spaCy` cannot load `en_core_web_sm`, the backend falls back to rule-based
  NLP behavior.
- If the backend install fails with a Windows file-lock error inside a fresh
  virtual environment, rerun the install outside sync-sensitive folders or close
  any editor, antivirus, or indexer that may be locking `site-packages`.

## Known Current Issues

- Minor mobile overflow handling for charts/tables on extremely narrow viewports (e.g., mobile devices below 360px width).
- Frontend unit/component test coverage is lighter than backend and pipeline coverage.
- The WebGL/R3F frontend build may emit a non-critical bundle-size warning.
- Fresh `npm install` currently reports a few dependency vulnerabilities in transitive frontend packages.
- Fresh backend dependency installation in this synced Windows workspace may hit a local file-lock issue during validation, which can be resolved by restarting editor/antivirus or running outside sync-sensitive folders.

