# Governance workflow

AlterScore separates the public deterministic assessment from retired
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
7. v1 `410 Gone`, unavailable analytics routes, and no retired-research
   imports in the serving graph;
8. frontend lint, exact-release build, v2 contract tests, Phase 7 separation,
   and Phase 8 release tests.
9. blocking backend quality/tests, serving-image build, readiness semantics,
   exact frontend/backend SHA parity, post-deploy smoke, and paired rollback
   verification.

## Research boundary

Historical synthetic labels, fairness reports, AUC values, explainers,
parsers, and training scripts are absent from the production branch. They are
recoverable from Git history but cannot add imports, artifacts, routes, feature
authorities, or dependencies to the public v2 image without a new reviewed
change and explicit authorization.

## Operational interpretation

`/api/live` is liveness and release identity, while `/api/ready` is the public
readiness contract. Readiness is based on the canonical instrument,
deterministic scorer, exact production release identity, signing, bounded
stores, and network rate limiter; it does not inspect ML artifacts.

CI is the deployment authority: a deployment may consume only the exact SHA
of a successful `AlterScore CI` workflow. Missing deployment credentials fail
closed. Docker and uptime monitoring require semantic readiness, not only an
HTTP status. Frontend and backend releases must carry the same SHA and frozen
contract versions, and the manual rollback workflow restores both targets
from one recorded release manifest.
