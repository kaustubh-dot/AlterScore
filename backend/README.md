# AlterScore Backend

FastAPI service for the manifest-backed AlterScore scoring runtime. It exposes
health, scoring, and analytics routes without retraining models at request
time.

## Runtime

- App import path: `backend.app.main:app`
- Production manifest: `models/registry/production_manifest.json`
- Active runtime: calibrated monotonic `XGBoost`
- API surface: `/api/health`, `/api/score`, and report-backed analytics routes
- Recommended Python: `3.12.x`

## Quick Start

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

Healthy manifest-backed startup reports `manifest_backed: true`,
`model_loaded: true`, and no missing or invalid scoring-critical artifacts.

## Tests

```bash
python -m pip install -r backend/requirements-dev.txt
ALTERSCORE_ENV=test python -m pytest
```

## Read Next

- [Project README](../README.md)
- [Setup](../docs/SETUP.md)
- [Deployment](../docs/DEPLOYMENT.md)
- [Backend runtime architecture](../docs/BACKEND_RUNTIME_ARCHITECTURE.md)
- [API contracts](../docs/API_CONTRACTS.md)
