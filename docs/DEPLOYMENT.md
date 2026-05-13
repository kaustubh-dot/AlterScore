# AlterScore Deployment

## Deployment Philosophy

AlterScore should be reproducible locally before it is deployed anywhere. Deployment must package a backend service, frontend build, and a complete production model artifact bundle.

## Deployment Stages

| Stage | Goal | Required Before Moving On |
|---|---|---|
| Local development | Fast iteration | Backend, frontend, and tests run locally |
| Local artifact serving | Validate model loading | Production manifest or direct runtime-model fallback loads in FastAPI |
| Local Docker | Package service | Health check passes in containers |
| Cloud demo | Public demo or evaluator deployment | Secrets, artifacts, logging, and rollback documented |
| Production pilot | Shadow-mode lender use | Real monitoring, audit, and retraining process |

## Runtime Components

- FastAPI backend.
- React frontend static build.
- Model artifact bundle.
- Generated analytics reports.
- Runtime logs.

## Environment Variables

| Variable | Example | Purpose |
|---|---|---|
| `ALTERSCORE_ENV` | `local` | Runtime environment label |
| `ALTERSCORE_API_VERSION` | `0.1.0` | Health/version reporting |
| `ALTERSCORE_REPO_ROOT` | repository root | Optional path override |
| `ALTERSCORE_MODEL_MANIFEST` | `models/registry/production_manifest.json` | Serving manifest |
| `ALTERSCORE_RUNTIME_MODEL_PATH` | `models/artifacts/logistic_best.pkl` | Local stub-model override when no production manifest is ready |
| `ALTERSCORE_REQUEST_LOG_PATH` | `backend/runtime/logs/requests.jsonl` | Append-only score-request JSONL path |
| `ALTERSCORE_LOG_LEVEL` | `INFO` | Backend log level |
| `ALTERSCORE_CORS_ORIGINS` | `http://localhost:5173` | Frontend origins |
| `VITE_API_BASE_URL` | `http://localhost:8000/api` | Frontend API base URL |

## Local Development Commands

The backend app entrypoint now exists at `backend/app/main.py`, and the health plus score route stubs can run locally against saved artifacts.

```powershell
# Backend
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Frontend
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

## Training And Artifact Promotion Flow

```text
Generate data
  -> Validate data
  -> Fit preprocessing and text PCA
  -> Train baselines
  -> Train classical models
  -> Train neural models
  -> Train stacking ensemble
  -> Calibrate ensemble
  -> Generate metrics, SHAP, DICE, fairness, PSI
  -> Create production manifest
  -> Run artifact loading smoke test
  -> Promote manifest
```

## Artifact Bundle Checklist

- [ ] `models/artifacts/calibrated_stacking.pkl`
- [x] `models/preprocessors/preprocessor.pkl`
- [x] `models/preprocessors/text_pca.pkl`
- [ ] `models/explainers/shap_explainer.pkl`
- [ ] `models/explainers/dice_explainer.pkl`
- [x] `models/reports/metrics.json`
- [x] `models/reports/baseline_metrics.json`
- [ ] `models/reports/fairness_report.json`
- [x] `models/reports/psi_report.json`
- [ ] `models/reports/global_importance.json`
- [x] `models/reports/population_percentiles.json`
- [ ] `models/registry/production_manifest.json`

## Backend Startup Requirements

At startup the backend must:

1. Load settings.
2. Resolve repository and artifact paths.
3. Load the production manifest when it exists, otherwise allow a local direct-model fallback for backend scoring stubs.
4. Validate artifact paths and detect missing scoring-critical files clearly.
5. Load model, preprocessor, and any available text PCA, explainers, and reports.
6. Expose `/api/health` with loaded and missing artifacts.
7. Fail clearly if scoring-critical artifacts such as the runtime model or preprocessor are missing.

## Current Stub Runtime Notes

- `backend/app/core/artifact_loader.py` now supports two modes:
  - production-manifest loading for the eventual serving bundle
  - `ALTERSCORE_RUNTIME_MODEL_PATH` fallback for the current local stub path
- The current scoring stub can run with saved logistic or classical artifacts plus the shared preprocessor.
- The current offline baseline and classical training commands now also persist `models/preprocessors/text_pca.pkl` from train months `1-8` only, using runtime-compatible raw embeddings derived from the saved synthetic dataset.
- The same offline training commands now persist `models/reports/population_percentiles.json` and expand `models/reports/metrics.json` with saved validation/test ROC, PR, calibration, and confusion payloads.
- The same offline training commands now also persist `models/reports/psi_report.json`, comparing train months `1-8` to test months `11-12` only across the canonical 35 model inputs with deterministic thresholds and saved per-feature statuses.
- `backend/app/main.py` now loads the runtime artifact bundle at startup and exposes `/api/health` plus `/api/score`.
- `backend/app/services/analytics.py` now serves `/api/model-stats` from `metrics.json` and `/api/baseline-comparison` from `baseline_metrics.json` without runtime retraining or ad hoc route-level file parsing.
- `backend/app/main.py` now also initializes the append-only request logging service for `/api/score`.
- `/api/health` currently returns `degraded` when scoring-critical artifacts are present but optional runtime artifacts such as SHAP, DICE, fairness, or PSI are still missing.
- When `models/preprocessors/text_pca.pkl` is present, request-time semantic dimensions now use the persisted PCA artifact; zero-filled semantic fallback remains only for intentionally PCA-less bundles and tests.
- When `population_percentiles.json` contains multiple model-specific tables, the runtime artifact loader now resolves the table for the active serving model so logistic fallback, classical fallback, and later manifest-backed ensemble serving can reuse one artifact format.
- Runtime artifact loading still succeeds when `psi_report.json` is present alongside the current local scoring bundle; the drift report remains optional for strict scoring readiness until the drift API route is added.
- If `metrics.json` or `baseline_metrics.json` is missing, the corresponding analytics endpoint now returns a structured `503` rather than recomputing reports inside the API process.
- SHAP and DICE artifacts do not exist yet, so the current stub scoring response returns empty `explanation` and `counterfactual_actions` lists.

## Runtime Foundation Files

- `.env.example` documents local environment variables.
- `backend/requirements.txt` pins the initial backend, ML, and test dependencies.
- `backend/app/core/settings.py` loads runtime settings from environment variables.
- `backend/app/core/paths.py` centralizes repository, data, model, report, and artifact paths.
- `frontend/package.json` and the Vite entry files provide the initial frontend package scaffold.

## Health Checks

### Liveness

- Endpoint: `GET /api/health`
- Pass condition: service process is running and returns JSON.

### Readiness

- Endpoint: `GET /api/health`
- Pass condition: `model_loaded` is true and required artifacts are present.

### Scoring Smoke Test

- Endpoint: `POST /api/score`
- Payload: known valid fixture from `tests/fixtures/score_request_valid.json`.
- Pass condition: status 200, score in 300-850, probability in 0-1, and the explanation/counterfactual fields are present even if the current stub returns empty lists before SHAP and DICE artifacts exist.

## Docker Plan

Expected structure:

```text
deploy/docker/
  backend.Dockerfile
  frontend.Dockerfile
  docker-compose.yml
```

Backend image must include only runtime dependencies and the artifact bundle path. Training dependencies may be separated later if image size becomes painful.

## Logging

Backend logs should include:

- Request ID.
- Endpoint.
- Status code.
- Latency.
- Model version.
- Artifact manifest version.
- Scoring failures with stack trace in server logs but sanitized client error.

Prediction logs should be append-only JSONL and must not store raw protected attributes as model inputs.
The current default path is `backend/runtime/logs/requests.jsonl`, overridable through `ALTERSCORE_REQUEST_LOG_PATH`.

## Rollback Plan

To roll back a model:

1. Keep previous `production_manifest.json` available.
2. Switch manifest pointer or redeploy previous artifact bundle.
3. Restart backend.
4. Verify `/api/health`.
5. Run scoring smoke test.
6. Record rollback in `docs/CURRENT_STATE.md` and `docs/MODEL_REGISTRY.md`.

## Production Pilot Notes

For a real MFI pilot, deployment should proceed in stages:

1. Shadow mode beside loan officer decisions.
2. Collect actual repayment outcomes for 6-12 months.
3. Retrain on real repayment labels.
4. Use model as recommendation with human final decision.
5. Consider autonomous decisions only for defined low-ticket loan thresholds after monitoring proves stability.
