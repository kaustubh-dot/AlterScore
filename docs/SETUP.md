# AlterScore setup

## Requirements

| Tool | Version | Purpose |
| --- | --- | --- |
| Python | `3.12.x` | Public backend and tests |
| Node.js | `20.19.x or >=22.12.0` | Frontend development and build |
| npm | `>=9 <12` | Frontend dependencies |

The public backend does not require model artifacts, Git LFS, scientific
packages, NLP models, or training dependencies. Those remain in the separate
offline archive environment described by
`research/legacy_synthetic_model/requirements-research.txt`.

## Backend

From the repository root:

```bash
python -m venv venv
# Windows: venv\Scripts\activate
python -m pip install -r backend/requirements.txt
```

Set a generated base64url signing secret and run the service:

```bash
# PowerShell example; use a secret manager for production.
$env:ALTERSCORE_SIGNING_SECRET = '<local-generated-secret>'
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Remote and production-like v2 form and score requests require HTTPS. Loopback
HTTP is accepted only in local/test/development environments, so the commands
above work without a development certificate. `/api/live` is liveness,
`/api/health` is a compatibility probe, and `/api/ready` reports semantic
readiness only when all six frozen checks pass.

## Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend reads `VITE_API_BASE_URL`. The deployed value is committed in
`frontend/.env.production`; the default relative `/api` proxy works over
loopback HTTP in local development. Non-loopback API origins must use HTTPS.

## Validation

```bash
python -m pip install -r backend/requirements.txt
python -m pip install -r backend/requirements-dev.txt
python -m pytest tests/unit/backend tests/integration/api
cd frontend
npm run lint
VITE_RELEASE_SHA=<40-character-reviewed-sha> npm run build
npm run test:phase5
npm run test:phase6
npm run test:phase7
npm run test:phase8
```

The inline `VITE_RELEASE_SHA=...` assignment uses POSIX shell syntax. In
PowerShell, set `$env:VITE_RELEASE_SHA = '<40-character-reviewed-sha>'` before
running `npm.cmd run build`.

## Key files

| File | Purpose |
| --- | --- |
| `backend/app/main.py` | Artifact-free public app entrypoint |
| `backend/app/api/v2/service.py` | Anonymous attempt, scoring, signing, and verification service |
| `backend/requirements.txt` | Serving-only dependency contract |
| `backend/requirements.lock` | Linux production serving dependencies with package hashes |
| `frontend/src/pages/ResearchLab.jsx` | Static offline-research boundary |
| `research/legacy_synthetic_model/` | Preserved synthetic-model archive |
| `docs/API_CONTRACTS.md` | Public v2 route and payload contract |
