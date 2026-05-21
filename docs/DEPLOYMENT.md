# AlterScore Deployment

## Deployment Philosophy

AlterScore should be reproducible locally before it is deployed anywhere.
Deployment must package three things together:

- the FastAPI backend
- the React frontend build
- the checked-in manifest-backed model bundle

## Current Deployment Readiness

- Local backend serving is implemented.
- Local frontend serving is implemented.
- Manifest-backed artifact loading is implemented.
- Docker and cloud deployment assets are not complete yet.

## Environment Variables

| Variable | Example | Purpose |
|---|---|---|
| `ALTERSCORE_ENV` | `local` | Runtime environment label |
| `ALTERSCORE_API_VERSION` | `0.1.0` | Health/version reporting |
| `ALTERSCORE_REPO_ROOT` | repository root | Optional path override |
| `ALTERSCORE_MODEL_MANIFEST` | `models/registry/production_manifest.json` | Serving manifest |
| `ALTERSCORE_RUNTIME_MODEL_PATH` | `models/artifacts/calibrated_stacking.pkl` | Explicit dev/test override path |
| `ALTERSCORE_REQUEST_LOG_PATH` | `runtime/logs/requests.jsonl` | Append-only request log path |
| `ALTERSCORE_LOG_LEVEL` | `INFO` | Backend log level |
| `ALTERSCORE_CORS_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Allowed frontend origins |
| `VITE_API_BASE_URL` | `http://127.0.0.1:8000/api` | Frontend API base URL |

## Local Development Commands

Run from the repository root:

```powershell
# Backend
& 'C:\Users\Kaustubh\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scripts\setup\check_environment.py
& 'C:\Users\Kaustubh\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m venv backend\.venv-cleanup
backend\.venv-cleanup\Scripts\python.exe -m pip install -r backend\requirements.txt
backend\.venv-cleanup\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000

# Frontend
cd frontend
& 'C:\Program Files\nodejs\npm.cmd' install
& 'C:\Program Files\nodejs\npm.cmd' run dev -- --host 127.0.0.1 --port 5173
```

## Validation Notes

- Python `3.12.x` is the recommended local backend interpreter family.
- Python `3.14.x` is not the recommended local setup path for this repository.
- During cleanup validation on May 22, 2026, backend dependency resolution
  succeeded in a fresh Python 3.12 environment, but the install in this synced
  Windows workspace hit a local file-lock error inside `site-packages` before a
  full clean-room startup could be completed.

## Artifact Bundle Checklist

### Core Runtime Artifacts

- [x] `models/artifacts/calibrated_stacking.pkl`
- [x] `models/preprocessors/preprocessor.pkl`
- [x] `models/preprocessors/text_pca.pkl`
- [x] `models/registry/production_manifest.json`

### Base Models

- [x] `models/artifacts/logistic_best.pkl`
- [x] `models/artifacts/rf_best.pkl`
- [x] `models/artifacts/xgb_best.pkl`
- [x] `models/artifacts/lgbm_best.pkl`
- [x] `models/artifacts/tabnet_epoch_best.zip`
- [x] `models/artifacts/mlp_best.pt`
- [x] `models/artifacts/calibrated_stacking_config.json`

### Explainability Artifacts

- [x] `models/explainers/shap_explainer.pkl`
- [x] `models/explainers/dice_explainer.pkl`

### Report Artifacts

- [x] `models/reports/metrics.json`
- [x] `models/reports/baseline_metrics.json`
- [x] `models/reports/fairness_report.json`
- [x] `models/reports/psi_report.json`
- [x] `models/reports/global_importance.json`
- [x] `models/reports/population_percentiles.json`

## Backend Startup Requirements

At startup the backend must:

1. Load settings.
2. Resolve repository-relative paths.
3. Prefer the production manifest for the default local runtime.
4. Validate manifest-declared checksums.
5. Load scoring-critical artifacts before serving `/api/score`.
6. Report loaded, missing, and invalid artifacts through `/api/health`.

## Health And Rollback

Minimum health checks:

- `GET /api/health` returns 200.
- `manifest_backed` is `true` for the checked-in bundle.
- `model_loaded` is `true`.

Rollback expectation for future deployments:

1. Restore the prior manifest-backed bundle.
2. Restart the backend.
3. Verify `/api/health`.
4. Run a score smoke test with `tests/fixtures/score_request_valid.json`.
5. Record the rollback in the handoff and state documents.

## Current Gaps Before Real Deployment

- `deploy/docker/` is still scaffolding only.
- `deploy/cloud/` is still scaffolding only.
- `deploy/monitoring/` is still scaffolding only.
- Release smoke docs need to be finalized after the dashboard work is complete.
