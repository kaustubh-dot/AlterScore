# AlterScore Deployment

## Deployment Philosophy

AlterScore should be reproducible locally before it is deployed anywhere. Deployment must package a backend service, frontend build, and a complete production model artifact bundle.

## Deployment Stages

| Stage | Goal | Required Before Moving On |
|---|---|---|
| Local development | Fast iteration | Backend, frontend, and tests run locally |
| Local artifact serving | Validate model loading | Production manifest loads in FastAPI |
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
| `ALTERSCORE_LOG_LEVEL` | `INFO` | Backend log level |
| `ALTERSCORE_CORS_ORIGINS` | `http://localhost:5173` | Frontend origins |
| `VITE_API_BASE_URL` | `http://localhost:8000/api` | Frontend API base URL |

## Local Development Commands

The backend dependency file and frontend package skeleton now exist. The backend app entrypoint is still pending, so the backend run command remains the intended local shape until that file is implemented.

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
- [ ] `models/preprocessors/preprocessor.pkl`
- [ ] `models/preprocessors/text_pca.pkl`
- [ ] `models/explainers/shap_explainer.pkl`
- [ ] `models/explainers/dice_explainer.pkl`
- [ ] `models/reports/metrics.json`
- [ ] `models/reports/baseline_metrics.json`
- [ ] `models/reports/fairness_report.json`
- [ ] `models/reports/psi_report.json`
- [ ] `models/reports/global_importance.json`
- [ ] `models/reports/population_percentiles.json`
- [ ] `models/registry/production_manifest.json`

## Backend Startup Requirements

At startup the backend must:

1. Load settings.
2. Resolve repository and artifact paths.
3. Load production manifest.
4. Validate all required artifact files exist.
5. Load model, preprocessor, text PCA, SHAP explainer, DICE explainer, and reports.
6. Expose `/api/health` with loaded and missing artifacts.
7. Fail clearly if scoring-critical artifacts are missing.

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
- Pass condition: status 200, score in 300-850, probability in 0-1, explanations returned.

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
