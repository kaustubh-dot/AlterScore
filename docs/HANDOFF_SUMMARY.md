# Handoff Summary: Stabilized Before Scoring Audit

**Date:** May 22, 2026
**Status:** Repository cleanup and setup normalization completed; scoring audit next
**Target Audience:** Contributors preparing for the scoring/debugging phase

## Backend Status

The backend runtime, API routes, checked-in artifacts, and manifest-backed
startup path should be treated as stable during this handoff phase. Do not
change scoring-critical files or the production manifest as part of cleanup-only
work.

## Stable API Surface

- `GET /api/health`
- `POST /api/score`
- `GET /api/model-stats`
- `GET /api/baseline-comparison`
- `GET /api/fairness-report`
- `GET /api/drift-report`
- `GET /api/global-importance`
- `GET /api/score-distribution`
- `GET /api/roc-data`
- `GET /api/pr-curve`
- `GET /api/calibration-curve`
- `GET /api/confusion-matrix`

## Frontend Status

Implemented:

- landing
- assessment
- processing
- results
- retry-safe submission
- sharing/export
- dashboard analytics panels for most report-backed endpoints

Pending:

- dashboard confusion-matrix rendering and independent panel states
- focused frontend tests
- formal browser QA evidence

## Local Startup

```powershell
# Terminal 1 - backend, from the repository root
backend\.venv-cleanup\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2 - frontend
cd frontend
& 'C:\Program Files\nodejs\npm.cmd' run dev -- --host 127.0.0.1 --port 5173
```

Health target: `http://127.0.0.1:8000/api/health`

## Validation Note

During this cleanup pass, a fresh Python 3.12 dependency resolution succeeded,
but the synced Windows workspace hit a local file-lock error during backend
installation before a full clean-room startup could be completed in the
temporary venv.

## Read Next

- `docs/SETUP.md`
- `docs/API_CONTRACTS.md`
- `docs/BACKEND_RUNTIME_ARCHITECTURE.md`
- `docs/TESTING_STRATEGY.md`
- `docs/ROADMAP.md`
