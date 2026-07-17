# Production rollback checklist

Rollback restores one coherent frontend/backend release pair from one exact
reviewed Git SHA. It does not restore a model manifest, serialized artifact,
explainer, or training bundle.

## Preconditions

- Identify the non-expired recorded release-manifest artifact and confirm `source_sha`,
  `frontend_release_sha`, and `backend_release_sha` are identical.
- Confirm the SHA is a previously reviewed release and the corresponding
  `ALTERSCORE_SIGNING_KEY_VERSION` is available.
- Confirm the Vercel and Hugging Face rollback credentials are configured and
  the provider's existing `/api/ready` signing check passes.
- Confirm the rollback reason and approver before starting the manual
  `rollback-release.yml` workflow.

## Automated paired rollback

Dispatch the manual workflow with the recorded SHA and confirmation:

```bash
gh workflow run rollback-release.yml \
  -f release_sha=<exact-40-character-reviewed-sha> \
  -f confirmation=ROLLBACK
```

The workflow shares one production-release queue with forward deployment,
first rejects a SHA without a non-expired post-smoke release-manifest artifact,
then checks out that exact SHA, requires all target credentials rather than
skipping, confirms existing signing readiness, rebuilds the secret-free backend
package, restores the backend and frontend from the same SHA, and runs the
paired release smoke runner.
Deployment execution remains separately authorized and is not part of normal
Phase 8 verification.

## Manual verification after restoration

1. Confirm the backend and frontend release metadata all report the selected
   SHA and frozen versions.
2. Confirm liveness and semantic readiness:

```bash
curl --fail https://<backend>/api/live
curl --fail https://<backend>/api/ready
python scripts/ci/smoke_release.py \
  --base-url https://<backend> \
  --frontend-url https://<frontend> \
  --expected-release-sha <exact-sha>
```

3. Confirm `/api/ready` reports `status=ready`, the frozen six checks in order,
   and six `pass` statuses.
4. Complete one HTTPS form/score/verification smoke test and confirm the
   verification response is redacted.
5. Confirm `POST /api/score` returns `410 Gone` and former analytics routes
   remain unavailable.
6. Record the rollback reason, selected SHA, signing-key reference, workflow
   run, and smoke result.

## Failure cases

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `/api/live` fails | Process or image startup failure | Inspect serving logs and restore the last reviewed pair. |
| `/api/ready` is `503` or not ready | Missing signing configuration, invalid release SHA, or serving-store/instrument failure | Restore the exact runtime configuration and inspect all six checks. |
| Frontend reports a release mismatch | Frontend/backend were not built from the same SHA | Restore the matching pair; do not bypass the client preflight. |
| Verification is unavailable | Bounded in-memory state was lost or expired | Treat the result as unavailable and issue a fresh attempt. |
| Smoke replay check fails | Single-use attempt boundary changed | Stop traffic and restore the last reviewed pair. |

Historical research artifacts are not a rollback authority for public scoring.
In-memory attempts and verification records are not durable across restart or
rollback; open attempts may need to be restarted.
Do not commit, push, deploy, or execute rollback without separate authorization.
