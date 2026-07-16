# Governance workflow

AlterScore separates the public deterministic assessment from offline
synthetic-model research.

## Public release gates

Every public release must verify:

1. frozen contract, assessment, and scoring-policy versions;
2. exact objective, judgment, branching, and legacy-transform arithmetic;
3. opaque single-use attempt IDs and HTTPS-only bearer transport;
4. signed results with redacted verification projections;
5. session-only detailed evidence with no token or raw submission persistence;
6. public-boundary language that excludes repayment, lending, approval,
   creditworthiness, pricing, and human-validation claims;
7. v1 `410 Gone`, unavailable analytics routes, and no archived-research
   imports in the serving graph;
8. frontend lint, production build, v2 contract tests, and Phase 7 separation
   tests.

## Research boundary

Archived synthetic labels, fairness reports, AUC values, explainers, parsers,
and training scripts are stored under `research/legacy_synthetic_model/`.
Labels and fairness data are synthetic. AUC measures recovery of generated data,
not external validation or repayment outcomes. The archived model does not
score public assessments.

Research work must use its separate requirements file and environment. It may
not add imports, artifacts, routes, feature authorities, or dependencies to
the public v2 image without a new reviewed phase and explicit authorization.

## Operational interpretation

`/api/live` is liveness, while `/api/ready` is the public readiness contract.
Readiness is based on the canonical instrument, deterministic scorer, signing,
bounded stores, and network rate limiter; it does not inspect ML artifacts.
Deployment credential gates, post-deploy automation, and full-release rollback
remain operational hardening work for Phase 8.
