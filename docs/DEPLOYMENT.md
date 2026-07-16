# Deployment

AlterScore deploys the public FastAPI v2 service to Hugging Face Spaces and
the React SPA to Vercel. Deploy both from the same reviewed release commit.

## Runtime boundary

The production Docker image installs only `backend/requirements.txt` and
allow-lists `backend/app`. It does not contain `models/`, `research/`,
`scripts/`, tests, frontend sources, serialized artifacts, explainers, NLP
packages, or training dependencies. The old synthetic model is retained only
under `research/legacy_synthetic_model/`.

Required environment values are:

```text
ALTERSCORE_ENV=production
ALTERSCORE_API_VERSION=0.2.0
ALTERSCORE_RELEASE_SHA=<exact deployed commit>
ALTERSCORE_SIGNING_SECRET=<base64url secret with at least 32 random bytes>
ALTERSCORE_CORS_ORIGINS=https://alterscore.vercel.app
```

Do not place the signing secret in the repository, frontend variables, image
layers, logs, or URLs. The v2 assessment rejects plaintext transport before a
bearer token is processed.

## Probes

- `/api/live` is the process liveness probe.
- `/api/health` is a temporary artifact-free compatibility probe for existing
  monitors.
- `/api/ready` is the v2 readiness contract and must report all six checks as
  `pass` before a public assessment is considered available.

Readiness does not inspect model files or research reports. It fails closed if
the signing configuration or serving stores are unavailable.

## Coordinated release checks

Run before release:

```bash
python -m pip install -r backend/requirements-dev.txt
python -m pytest tests/unit/backend tests/integration/api/test_phase4_secure_anonymous_api.py tests/integration/api/test_phase7_legacy_retirement.py
cd frontend && npm run lint && npm run build && npm run test:phase5 && npm run test:phase6 && npm run test:phase7
```

Then verify the deployed v2 form, score, and redacted result-verification
routes using the exact release metadata. A frontend-only or backend-only
release is not a coherent public release.

Deployment credential gating, post-deploy smoke automation, readiness monitor
migration, and whole-release rollback automation remain operational hardening
work for Phase 8.
