# AlterScore Deployment

AlterScore deploys the backend and frontend separately from the same GitHub
repository.

## Current Production Targets

| Component | Target | Source |
|---|---|---|
| Backend API | Hugging Face Spaces Docker app | `.github/workflows/deploy-hf.yml` |
| Frontend SPA | Vercel | `frontend/vercel.json` and Vercel Git integration |

Backend deployment packages only what the API needs: `backend/`, `models/`,
`scripts/`, `Dockerfile`, and a minimal Hugging Face Space README.

## Backend Deployment

On push to `main`, `.github/workflows/deploy-hf.yml` builds a Hugging Face
Space package and force-pushes it to the configured Space when `HF_TOKEN` is
available in GitHub secrets.

Required GitHub secret:

| Secret | Purpose |
|---|---|
| `HF_TOKEN` | Push access to the Hugging Face Space |

The deployed backend starts through the root `Dockerfile` and loads
`models/registry/production_manifest.json`.

## Frontend Deployment

Vercel builds `frontend/` from the GitHub repository. The SPA rewrite rule in
`frontend/vercel.json` sends client-side routes to `index.html`.

Production API configuration is committed in `frontend/.env.production`:

```text
VITE_API_BASE_URL=https://coolbot22-alterscore-backend.hf.space/api
```

`VITE_*` values are public build-time values, not secrets.

## Runtime Artifact Bundle

The active production manifest is `xgboost_monotonic_calibrated_v4`
(`model_version` `0.7.0`). It checksum-locks:

- `models/artifacts/xgboost_monotonic.pkl`
- `models/preprocessors/preprocessor_monotonic.pkl`
- `models/preprocessors/text_pca.pkl`
- `models/explainers/shap_explainer_monotonic.pkl`
- `models/explainers/dice_explainer_monotonic.pkl`
- `models/reports/metrics_monotonic.json`
- `models/reports/baseline_metrics_monotonic.json`
- `models/reports/fairness_report_monotonic.json`
- `models/reports/psi_report_monotonic.json`
- `models/reports/global_importance_monotonic.json`
- `models/reports/population_percentiles_monotonic.json`

Do not remove or regenerate these files without updating
`production_manifest.json` and rerunning the promotion gates.

## Release Checks

Run these before merging deployment-affecting changes:

```bash
ALTERSCORE_ENV=test python -m pytest
python scripts/validation/verify_reproducibility.py
python -m backend.ml.registry.promotion_gates --manifest models/registry/production_manifest.json --allow-promoted-incompatibility
cd frontend && npm run build
```

## Health Checks

Backend:

```bash
curl https://coolbot22-alterscore-backend.hf.space/api/health
```

Expected:

- `status` is `ok`
- `manifest_backed` is `true`
- `model_loaded` is `true`
- no scoring-critical missing or invalid artifacts

Frontend:

- Vercel build succeeds
- deployed app can call `/api/health` through `VITE_API_BASE_URL`
- assessment flow can submit to `/api/score`

## Rollback

Rollback is manifest-based. Restore the last known-good manifest and all
artifact files referenced by its `artifacts` block, then rerun health and score
smoke checks. See [Rollback checklist](ROLLBACK_CHECKLIST.md).
