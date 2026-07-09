# AlterScore Setup

This is the contributor setup path for the deployed AlterScore repository.

## Requirements

| Tool | Required | Notes |
|---|---|---|
| Python | `3.12.x` | Backend runtime and tests |
| Node.js | `>=18 <25` | Frontend development/build |
| npm | `>=9 <12` | Use `npm.cmd` on Windows PowerShell if needed |
| Git LFS | Recommended | Required when cloning model artifacts from GitHub |

The backend pins `scikit-learn==1.5.1` for compatibility with the checked-in
runtime artifacts. Do not upgrade it without retraining and replacing the model
bundle.

## Backend

Run from the repository root:

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt
python -m spacy download en_core_web_sm
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Health check:

```bash
curl http://127.0.0.1:8000/api/health
```

Expected healthy state:

- `manifest_backed` is `true`
- `model_loaded` is `true`
- `missing_artifacts` and `invalid_artifacts` are empty for scoring-critical files

## Frontend

In a second terminal:

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

The production frontend uses `frontend/.env.production`. For local overrides,
create `frontend/.env.local` with:

```text
VITE_API_BASE_URL=http://127.0.0.1:8000/api
```

## Validation

Backend:

```bash
ALTERSCORE_ENV=test python -m pytest
python scripts/validation/verify_reproducibility.py
python -m backend.ml.registry.promotion_gates --manifest models/registry/production_manifest.json --allow-promoted-incompatibility
```

Frontend:

```bash
cd frontend
npm run lint
npm run build
```

## Key Files

| File | Purpose |
|---|---|
| `README.md` | Project overview and quickstart |
| `backend/requirements.txt` | Backend runtime dependencies |
| `backend/requirements-dev.txt` | Backend test dependencies |
| `frontend/package.json` | Frontend scripts and dependencies |
| `frontend/package-lock.json` | Reproducible frontend install |
| `.env.example` | Backend environment variable examples |
| `models/registry/production_manifest.json` | Runtime artifact contract |

## More Documentation

- [Deployment](DEPLOYMENT.md)
- [API contracts](API_CONTRACTS.md)
- [Backend runtime architecture](BACKEND_RUNTIME_ARCHITECTURE.md)
- [Governance workflow](GOVERNANCE_WORKFLOW.md)
- [Model registry](MODEL_REGISTRY.md)
- [Project structure](PROJECT_STRUCTURE.md)
