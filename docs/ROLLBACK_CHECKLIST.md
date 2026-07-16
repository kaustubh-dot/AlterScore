# Production rollback checklist

The public runtime is a deterministic v2 application. Rollback restores one
coherent frontend/backend release commit; it does not restore a model
manifest, serialized artifact, explainer, or training bundle.

## Procedure

1. Identify the last reviewed release commit and its frontend/backend release
   metadata.
2. Redeploy that exact commit to the backend and frontend targets.
3. Supply the matching `ALTERSCORE_RELEASE_SHA` and signing configuration from
   the deployment secret store.
4. Confirm liveness and readiness:

```bash
curl -f https://<backend>/api/live
curl -f https://<backend>/api/ready
```

5. Confirm `/api/ready` reports the frozen contract versions and six passing
   checks.
6. Complete one HTTPS form/score/verification smoke test and confirm the
   verification response remains redacted.
7. Confirm `POST /api/score` still returns `410 Gone` and former analytics
   routes remain unavailable.
8. Record the rollback reason and exact release SHA. Commit/push operations
   require separate authorization.

## Failure cases

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `/api/live` fails | Process or image startup failure | Inspect serving image logs and restore the last reviewed release. |
| `/api/ready` is `503` | Missing signing secret or serving-store/instrument failure | Restore the exact secret/configuration and inspect the six allow-listed checks. |
| Form route is unavailable | Signing readiness or instrument failure | Do not bypass the error; roll back the coherent release pair. |
| Verification is unavailable | Bounded in-memory state was lost or expired | Treat the result as unavailable and issue a fresh attempt. |
| Frontend cannot reach the API | HTTPS, CORS, or release mismatch | Compare the frontend base URL and backend release metadata. |

Research artifacts under `research/legacy_synthetic_model/` are not a rollback
authority for public scoring.
