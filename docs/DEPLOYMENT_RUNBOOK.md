# AlterScore Production Manual Deployment Runbook

This document serves as the comprehensive manual deployment, operation, and rollback runbook for the non-dockerized **AlterScore** platform.

---

## 1. System Requirements

* **OS:** Windows Server 10/11 or Windows 10/11 Professional
* **Python Runtime:** Python `3.12.x` (Recommended; Python `3.14.x` is not supported due to dependency compilation locks)
* **NodeJS Runtime:** Node.js `v18.x` to `v24.x`
* **Network Ports:**
  * **Backend Service:** Port `8000` (default)
  * **Frontend Service:** Port `5173` (development/preview) or Port `80` (production server)

---

## 2. Environment Variables & Configurations

Create a `.env` file at the repository root with the following production variables:

```bash
# Backend Configs
ALTERSCORE_ENV=production
ALTERSCORE_API_VERSION=0.2.0
ALTERSCORE_REPO_ROOT=.
ALTERSCORE_MODEL_MANIFEST=models/registry/production_manifest.json
ALTERSCORE_REQUEST_LOG_PATH=runtime/logs/requests.jsonl
ALTERSCORE_LOG_LEVEL=INFO
ALTERSCORE_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000

# Frontend Configs (frontend/.env)
VITE_API_BASE_URL=http://127.0.0.1:8000/api
```

---

## 3. Step-by-Step Deployment Guide

### Step 3.1: Clean-room Workspace Setup

Initialize a clean local state by ensuring no cache leftovers or build directories are present:
```powershell
# Clean python and npm directories
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue backend/__pycache__
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue tests/__pycache__
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue frontend/dist
```

### Step 3.2: Backend Deployment

1. Initialize a dedicated virtual environment:
   ```powershell
   py -3.12 -m venv venv
   ```
2. Activate and install production dependencies:
   ```powershell
   venv\Scripts\python.exe -m pip install --upgrade pip
   venv\Scripts\python.exe -m pip install -r backend/requirements.txt
   ```
3. Run backend tests to verify environment consistency:
   ```powershell
   venv\Scripts\pytest -v tests/integration/api/test_checked_in_runtime_bundle_smoke.py
   ```
4. Start the ASGI server (Uvicorn) under a process supervisor or direct host:
   ```powershell
   venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --workers 4
   ```

### Step 3.3: Frontend Deployment

1. Navigate to the `frontend/` directory and install dependencies:
   ```powershell
   cd frontend
   npm install
   ```
2. Run frontend unit tests to ensure styling and payload structures are valid:
   ```powershell
   npm run test
   ```
3. Build the production assets:
   ```powershell
   npm run build
   ```
4. Serve the production bundle using local node server or reverse proxy:
   ```powershell
   npm run preview -- --host 127.0.0.1 --port 5173
   ```

---

## 4. Post-Deployment Verification Checklist

Execute these smoke checks immediately after starting both services:

- [ ] **API Health Check:** Query `http://127.0.0.1:8000/api/health` and verify the JSON response contains:
  * `"status": "ok"`
  * `"model_loaded": true`
  * `"manifest_backed": true`
  * `"manifest_version": "xgboost_monotonic_v1"`
- [ ] **Scoring Endpoint Verification:** Send a test payload to `/api/score`:
  ```powershell
  Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/score" -Method Post -InFile "tests/fixtures/score_request_valid.json" -ContentType "application/json"
  ```
  Verify it returns a `300-850` score, SHAP explanation factors, and DICE counterfactual recommendations.
- [ ] **Analytics Coverage:** Ensure the Evaluator dashboard loads and resolves curves, baseline graphs, and the newly added **confusion matrix** without JS console exceptions.

---

## 5. Rollback Procedures

If a promoted manifest model demonstrates high drift, poor calibration, or high subgroup disparity, execute a rollback to the stable stacking ensemble:

1. **Modify Manifest Target:** Change `"ALTERSCORE_MODEL_MANIFEST"` to the backup calibrated stacking manifest configuration.
2. **Reload Backend Service:** Restart the uvicorn process. The system loads base classifiers lazy-loaded at startup.
3. **Verify Health:** Verify that `/api/health` reports status `ok` and version maps to `stacking_ensemble_v0.2.0`.
4. **Audit Predictions:** Resubmit the validation fixture payload to confirm score outputs match baseline expectation curves.
