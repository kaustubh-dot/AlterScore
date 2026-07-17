# Backend runtime architecture

The production backend is a small, artifact-free FastAPI service. Its import
graph is limited to the public v2 API, canonical instrument, branching engine,
unified deterministic scorer, standard-library security stores, and FastAPI /
Pydantic serving dependencies.

## Startup path

1. `backend.app.main:create_app` loads CORS, release metadata, and the signing
   secret from environment settings.
2. The lifespan creates `AnonymousAssessmentService`.
3. No model manifest, serialized artifact, research report, NLP model, or
   legacy request logger is read during import or startup.
4. `/api/live` reports process liveness. `/api/ready` checks the canonical
   instrument, deterministic scorer, signing configuration, bounded attempt and
   verification stores, and v2 network limiter.

Readiness is therefore independent of model artifacts. A missing signing
secret makes the service fail closed for scoring, but never causes a research
artifact lookup.

## Public request path

The v2 service issues a seeded server-side form, translates only the issued
opaque IDs, scores through `backend.app.unified_scoring`, signs the public
projection, and stores only the redacted verification record. Branching
transitions and objective answer keys remain server-side in the canonical
instrument package.

The middleware temporarily captures the network host only for the salted v2
rate-limit hash, then redacts the ASGI client tuple before access logging.
Successful detailed explanations are returned only on the score response;
verification remains a redacted public proof.

## Retired and isolated surfaces

`POST /api/score` and `/api/debug-score` are dependency-free `410 Gone`
tombstones. Former analytics routes are not registered. The old scorer,
artifact loader, parsers, explainers, training scripts, serialized models, and
legacy tests live under `research/legacy_synthetic_model/` and are not
imported by `backend/app`.

The frontend Research Lab is static and direct-link-only. It describes the
archive without making network calls, reading result state, or influencing
public scoring.

## Production image boundary

`Dockerfile` installs only the hash-verified Linux `backend/requirements.lock` and
copies only `backend/app` plus the serving dependency contract. `.dockerignore`
excludes source, tests, model artifacts,
research, scripts, data, and local runtime output as defense in depth. The
research requirements file is for a separate offline environment and is never
installed in production.
