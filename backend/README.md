# AlterScore Backend

The backend is a FastAPI service that serves the checked-in manifest-backed
runtime bundle in `models/`. It exposes health, scoring, and analytics routes
without retraining models at request time.

## Working State

- Startup path: `backend.app.main:app` from the repository root
- Default artifact source: `models/registry/production_manifest.json`
- Runtime bundle: calibrated stacking ensemble plus six base models
- API surface: `/api/health`, `/api/score`, and report-backed analytics routes
- Recommended local Python: `3.12.x`

## Backend Quick Start

Run these commands from the repository root:

```powershell
& 'C:\Users\Kaustubh\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' scripts\setup\check_environment.py
& 'C:\Users\Kaustubh\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m venv backend\.venv-cleanup
backend\.venv-cleanup\Scripts\python.exe -m pip install -r backend\requirements.txt
backend\.venv-cleanup\Scripts\python.exe -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

If you already have a local project venv, replace `backend\.venv-cleanup` with
your preferred environment path.

## Environment Notes

- `backend/requirements.txt` contains the runtime stack only.
- `backend/requirements-dev.txt` layers test dependencies on top of runtime.
- The checked-in artifacts currently require `scikit-learn>=1.8,<1.9`.
- Python `3.14.x` is not part of the supported local setup path for this repo.

## Health Check

Once the service is running:

```powershell
curl http://127.0.0.1:8000/api/health
```

Healthy manifest-backed startup should report:

- `status: "ok"`
- `manifest_backed: true`
- `model_loaded: true`
- empty `missing_artifacts` and `invalid_artifacts`

## Read Next

- [`README.md`](../README.md)
- [`docs/SETUP.md`](../docs/SETUP.md)
- [`docs/BACKEND_RUNTIME_ARCHITECTURE.md`](../docs/BACKEND_RUNTIME_ARCHITECTURE.md)
- [`docs/API_CONTRACTS.md`](../docs/API_CONTRACTS.md)
- [`docs/DEPLOYMENT.md`](../docs/DEPLOYMENT.md)
