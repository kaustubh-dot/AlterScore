# Deployment

AlterScore releases the public FastAPI v2 service and React SPA as one
coherent release. Deployment is only invoked by the CI-gated workflow or an
explicitly authorized manual rollback; this Phase 9 audit did not deploy.

## Release identity

Every release uses one exact 40-character lowercase Git SHA:

```text
contract_version=2.0
assessment_version=india-en-3.0.0
scoring_policy_version=readiness-rubric-1.0.0
source_sha=<exact reviewed commit>
frontend_release_sha=<same exact reviewed commit>
backend_release_sha=<same exact reviewed commit>
```

The frontend CI job requires `VITE_RELEASE_SHA=$GITHUB_SHA` before building.
Vercel must provide the same value for its production build. The frontend
rejects missing or local production release values and preflights the backend
`/api/live` metadata before issuing a form request.

The backend image receives `ALTERSCORE_RELEASE_SHA` through the Docker build
argument. Production readiness also requires a non-local
`ALTERSCORE_SIGNING_KEY_VERSION` and a valid `ALTERSCORE_SIGNING_SECRET`.
The signing secret is never stored in source, the frontend, image layers, or
the generated package. The generated Hugging Face package contains a
secret-free `release-metadata.json` with the release and key-version reference.

Required backend runtime values:

```text
ALTERSCORE_ENV=production
ALTERSCORE_API_VERSION=0.2.0
ALTERSCORE_RELEASE_SHA=<exact deployed commit>
ALTERSCORE_SIGNING_SECRET=<base64url secret with at least 32 random bytes>
ALTERSCORE_SIGNING_KEY_VERSION=<non-local key reference>
ALTERSCORE_CORS_ORIGINS=https://alterscore.vercel.app
```

## CI and deployment gates

`AlterScore CI` is blocking for Python quality, frontend lint, the production
release-SHA gate, the Phase 5–9 frontend tests, the complete backend suite,
the serving-image build, and the frozen release-contract scan.

`deploy-hf.yml` accepts only a successful trusted `push` run from this
repository's `main` branch. It rejects stale successful runs whose SHA is no
longer the `main` tip, serializes with rollback in one production-release
queue, checks out that exact SHA, and requires the Hugging Face, Vercel,
signing-key-version, signing-secret, and frontend configuration values before
changing either target. Missing credentials fail the job; they are never
treated as a successful skip.

The trusted release workflow builds and promotes the Vercel production bundle
from the same reviewed SHA with `VITE_RELEASE_SHA` set to that SHA. Disable
provider-side Git auto-promotion for the production Vercel target; the
workflow is the deployment authority. The canonical production target is
bound in the reviewed workflow, while the Vercel CLI's unique deployment URL
is captured and smoke-tested independently before the canonical alias.

The Vercel CLI is version-pinned in both forward deployment and rollback so a
mutable `latest` package is not executed with production credentials.

Before any deployment or rollback, configure the hosting provider with the
same signing secret stored in the Actions secret store. The workflow checks
that the existing public `/api/ready` signing check passes before it publishes
a package, so missing or invalid provider signing configuration fails before a
new release is pushed. The package itself binds the non-secret signing-key
version and never contains the signing secret.

## Runtime probes

- `/api/live` is the process liveness and release-metadata probe.
- `/api/health` remains a compatibility route for existing callers.
- `/api/ready` is the public v2 readiness contract.

The Docker healthcheck and scheduled monitor call `/api/ready` and require
HTTP success, `status=ready`, the frozen six check names in order, and every
check to report `pass`. A degraded or not-ready scorer cannot appear healthy.
Readiness does not inspect model files or archived research.

## Post-deploy smoke

The deployment workflow runs the standard-library smoke runner after the
backend package is published and the frontend target is available:

```bash
python scripts/ci/smoke_release.py \
  --base-url https://coolbot22-alterscore-backend.hf.space \
  --frontend-url https://alterscore.vercel.app \
  --expected-release-sha <exact reviewed commit>
```

It checks live/readiness metadata, readiness semantics, the frozen 18-plus-6
form shape, wrong-version rejection, a valid score, redacted verification,
single-use replay rejection, and the exact release/version fragments in the
frontend bundle. Response bodies, tokens, submissions, and secrets are never
printed.

After a successful paired smoke, the workflow uploads a concrete secret-free
release-manifest artifact derived from
`docs/RELEASE_MANIFEST_TEMPLATE.json`. Record its workflow URL with the
release. Rollback queries for the non-expired `release-manifest-<SHA>` artifact
before checkout, so it cannot restore a SHA that has not completed a paired
post-smoke forward release.

## Rollback

`rollback-release.yml` is manual only. It requires the exact SHA from a
non-expired verified release-manifest artifact, explicit `ROLLBACK`
confirmation, HF credentials, Vercel credentials, signing-key version, and
the bound canonical frontend URL. The validation job checks manifest field parity,
target URLs, smoke status, workflow provenance, package identity, and exact
SHA before checkout. It builds the backend package and frontend from the same
SHA, restores both targets, and runs the paired smoke checks. Use it only
after recording the release manifest and rollback reason.

Attempts and verification records are bounded in memory. A restart or rollback
can invalidate in-flight attempt tokens and make prior verification links
unavailable; issue a fresh form after the pair is healthy.

Do not place signing material in repository variables, frontend variables,
image layers, logs, URLs, or release metadata. Commit, push, deploy, and
rollback execution require separate authorization from this implementation.
