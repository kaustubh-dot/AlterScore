# Production Rollback Checklist

Use this checklist when reverting a bad backend model/runtime deployment.
Rollback is manifest-based: the manifest and every artifact it references must
move together.

## Active Manifest

| Field | Value |
|---|---|
| `manifest_version` | `xgboost_monotonic_calibrated_v4` |
| `model_version` | `0.7.0` |
| `runtime_model_name` | `xgboost_monotonic` |
| `runtime_model_type` | `classical_monotonic` |
| `promotion_status` | `promoted` |

## Procedure

1. Find the last known-good manifest commit.

```bash
git log --oneline --follow -- models/registry/production_manifest.json
```

2. Restore the manifest and every artifact path declared in its `artifacts`
   block.

```bash
git checkout <good-commit> -- models/registry/production_manifest.json models/artifacts models/preprocessors models/explainers models/reports
```

3. Verify promotion gates and checksums.

```bash
python -m backend.ml.registry.promotion_gates --manifest models/registry/production_manifest.json --allow-promoted-incompatibility
```

4. Start the backend locally.

```bash
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

5. Verify health.

```bash
curl http://127.0.0.1:8000/api/health
```

Expected:

- `manifest_backed` is `true`
- `model_loaded` is `true`
- `model_version` matches the rollback target
- no scoring-critical missing or invalid artifacts

6. Smoke test scoring with `tests/fixtures/score_request_valid.json`.

7. Commit the rollback with the manifest version and reason in the commit
   message. If the rollback becomes permanent, update `docs/MODEL_REGISTRY.md`
   and `docs/DEPLOYMENT.md`.

## Failure Cases

| Symptom | Likely Cause | Fix |
|---|---|---|
| Checksum validation fails | Manifest and artifacts do not match | Restore all manifest-declared files from the same commit |
| `/api/health` reports missing artifacts | Deployment package is incomplete | Check `.github/workflows/deploy-hf.yml` package step |
| `/api/score` returns 503 | Scoring-critical artifact missing or invalid | Inspect `/api/health` and backend logs |
| Frontend cannot score | API base URL or CORS mismatch | Check `frontend/.env.production` and backend CORS settings |
