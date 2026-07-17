# AlterScore v3 final audit

## Handoff status

This report records Luna's Phase 9 implementation and Codex's independent
final audit on branch `codex/scoring-production-hardening`, reviewed from base
HEAD `e5e9af7b86de8a8008c08cb51079072313d02c7d`. Codex's decision is **PASS**:
the branch is a functional portfolio release candidate with no known blocking
scoring, API, frontend, or release-automation defect after the corrections
below. The final reviewed change set is committed and pushed after this record.

No deployment, rollback, reset, branch switch, or model-artifact regeneration
was performed. The review prompt was included as project documentation. The
pre-existing `runtime/shared_session_trained_model_answer_only_v2/` bundle was
preserved locally and is now covered by the runtime-model ignore rule.

## Architecture and public boundaries

- `backend/app/instrument/` owns the generated public instrument and server-only
  answer authority.
- `backend/app/branching/` owns the two deterministic three-stage financial
  state simulations and their conservation rules.
- `backend/app/unified_scoring/` composes the canonical score and explanation.
- `backend/app/api/v2/` owns HTTPS form issuance, one-time attempts, signed
  scoring, redacted verification, readiness, and rate limits.
- `frontend/src/` renders the issued form and signed explanation but has no score
  authority, answer key, rubric, generation rule, or model dependency.
- `research/legacy_synthetic_model/` is outside the serving graph and remains a
  clearly labelled synthetic offline demonstration.

The only public scoring claims are the Financial Decision Readiness Index and
its illustrative `legacy_demo_score` transformation. The system does not claim
to predict repayment, establish creditworthiness, approve lending, determine
eligibility, price credit, or represent a validated psychometric instrument.

Frozen versions:

```text
contract_version: 2.0
assessment_version: india-en-3.0.0
scoring_policy_version: readiness-rubric-1.0.0
```

## Question inventory and formulas

Each issued form contains 18 scored items and six diagnostic items:

- eight generated integer objective concepts;
- four static single-choice judgment scenarios;
- six path-independent branching stages across two three-stage simulations;
- six `Never / Rarely / Sometimes / Often / Always / Not applicable` behavior
  profile items, which are diagnostic only;
- one optional narrative field, which is not scored, classified, retained, or
  logged.

The frozen formulas are:

```text
objective_score = 100 * correct_objective_answers / 8
static_sjt_score = 100 * rubric_points / 3
branching_scenario_score =
    0.40 * obligation_coverage
  + 0.25 * liquidity_retention
  + 0.20 * cost_efficiency
  + 0.15 * plan_feasibility
judgment_score = mean(four static_sjt_scores, two branching_scenario_scores)
financial_decision_index = round_half_up(
    0.55 * objective_score + 0.45 * judgment_score
)
legacy_demo_score = 300 + floor(5.5 * financial_decision_index + 0.5)
```

Exact rational contributions and explanation digests reconcile the displayed
scores, the final index, all eight worked objective calculations, four
principle-level SJT explanations, and both branching timelines. Behavior,
narrative, telemetry, timing, device, ordering, and revision data do not affect
the score.

## Anonymous threat model

The boundary protects against invented IDs, cross-attempt answers, altered
forms, token tampering, replay, duplicate JSON keys, oversized/deep/non-finite
payloads, edited result projections, result-signature tampering, explanation
digest mismatch, public answer/rubric leakage, bearer-token logging, and
unbounded verification probing. Attempts are freshly generated, opaque,
single-use, signed, bounded, and rate-limited. Verification exposes only a
redacted signed projection and now shares the HTTPS and rate-limit boundary
with form and score routes.

The boundary cannot prove identity or prevent calculators, search, another
person answering, screenshots, multiple devices, distributed black-box
probing, or intentional self-report fabrication. The score therefore measures
demonstrated knowledge and judgment for one anonymous attempt, not real-world
behavior or credit risk.

## Phase 9 corrections

The audit closed these in-scope findings:

- verification now fails closed on plaintext transport and uses its own abuse
  bucket;
- cached detailed and summary results require the exact current frontend SHA;
- browser storage reads/writes/removals tolerate disabled or revoked storage;
- reduced-motion handling covers Lenis, count-up, cursor, and magnetic motion;
- client errors no longer render untrusted upstream detail text;
- HTTPS public responses include HSTS;
- release manifests are generated from the frozen template and validate exact
  SHA/version/URL/smoke/provenance fields before rollback;
- release packaging rejects unsafe key references, Dockerfile symlinks, and
  hanging Git subprocesses;
- smoke checks assert the configured CORS origin on public success and error
  paths;
- the CI formatter gate includes the Phase 9 regression test.

Codex's final review additionally closed these defects:

- repaired the EMI partial-deferral transition so it actually pays 300 units,
  clears the 450-unit essential-expense balance, and carries exactly 150 units;
- added all decision-relevant starting and path-dependent facts to both
  branching prompts;
- corrected implausible SJT partial-credit ordering for late rent protection,
  loss-making runway, and fee-only borrowing comparisons;
- allowed plaintext form/score/verification only on a captured loopback host in
  local/test/development, while remote and production-like HTTP still fail
  closed;
- applied HSTS to every public API response, including proxy deployments whose
  ASGI scheme is not rewritten;
- bound the canonical Vercel target in code, captured the unique deployment URL,
  and required smoke success against both origins;
- pinned all third-party GitHub Actions to immutable commit SHAs;
- added a hash-locked Linux production dependency graph and required it in CI,
  Docker, and the allow-listed Hugging Face package;
- updated the frontend lock from vulnerable `form-data` 4.0.5 to 4.0.6;
- made the diagnostic self-reflection visible once in the immediate result,
  while continuing to omit it from browser history, session retention, score,
  and signed verification.

## API migration and release operations

The active API is `/api/v2/assessment/form`,
`/api/v2/assessment/score`, and `/api/v2/results/verify/{result_id}`, supported
by `/api/live` and `/api/ready`. The model-backed `/api/score` and
`/api/debug-score` routes return `410 Gone`; `/api/v1/score` and former
analytics routes are absent. The frontend uses only the v2 transport and keeps
the bearer token in memory.

Forward release accepts only a successful same-repository `push` CI run for
the current `main` tip, builds both targets from the exact SHA, requires
provider credentials and signing readiness, runs paired smoke checks, and
uploads a secret-free manifest. Manual rollback requires explicit confirmation
and a non-expired manifest whose exact SHA, URLs, smoke status, package
identity, workflow provenance, and frozen versions validate before publishing
either target.

## Dependency and artifact inventory

- Serving backend: FastAPI 0.115.6, Uvicorn 0.34.3, Pydantic 2.10.6.
- Test-only backend additions: pytest 8.4.2 and httpx 0.28.1.
- Frontend: React 19.2.6, React Router 7.17.0, Axios 1.17.0, Lenis 1.3.23,
  Lucide React 1.17.0, Vite 8.x, with npm lockfile version 3.
- Production Docker installs only hash-verified
  `backend/requirements.lock`, copies only `backend/app` and the serving
  dependency contract, and uses a digest-pinned Python 3.12-slim image; active
  model files are not required.
- Workflows: `ci.yml`, `deploy-hf.yml`, `keepalive.yml`, and
  `rollback-release.yml`.
- The separated research archive contains 120 files and is not in the serving
  import or image graph. The preserved local test-only runtime bundle has 10
  files (140,617 bytes), is ignored, and is not promoted or copied into
  production.
- The active `models/` tree has no serving artifact inventory; model-backed
  research artifacts remain archived or outside the public runtime.

## Verification record

| Command | Result |
|---|---|
| Bundled Python full pytest | PASS: 242 passed in 8.38s |
| Focused scoring, branching, secure API, release, and final-audit suite | PASS: 67 passed in 8.02s, followed by 4/4 final-audit lock tests |
| `npm.cmd run lint` | PASS |
| `npm.cmd run test:phase5` | PASS: 11 passed |
| `npm.cmd run test:phase6` | PASS: 7 passed |
| `npm.cmd run test:phase7` | PASS: 3 passed |
| `npm.cmd run test:phase8` | PASS: 4 passed |
| `VITE_RELEASE_SHA=<40-char reviewed SHA> npm.cmd run build` | PASS: Vite 8.0.16; 1,842 modules transformed |
| `npm.cmd audit --omit=dev --audit-level=high` | PASS: 0 vulnerabilities after lock update |
| Production Linux `pip install --dry-run --require-hashes` | PASS: all locked packages and hashes resolved for CPython 3.12/manylinux x86-64 |
| Ruff check on `backend tests scripts/ci` | PASS |
| Ruff format check on audited Python paths | PASS: 15 files formatted |
| YAML parse for CI, deployment, and rollback workflows | PASS |
| Local browser acceptance | PASS: two complete 25-item attempts, randomized forms, repaired branch replay, signed result, ephemeral self-reflection, refresh behavior, and 390 px mobile result |
| Public deployment inspection | DRIFT FOUND: `https://alterscore.vercel.app` still serves the retired model/credit-score experience; deployment was not authorized in this audit |
| `git diff --check` | PASS; only Git line-ending and inaccessible global-ignore warnings |

## Remaining limitations and future validation

Docker image construction could not run locally because Docker is unavailable.
Live provider smoke, deployment, rollback, and trusted-proxy production
verification were not run; they require external authority or unavailable
tooling. The currently deployed public site is the retired system and must be
replaced through the reviewed paired-release workflow before this branch is
publicly live. Forward backend-then-frontend publication is
serialized and compensated by smoke/rollback, but the two external providers
do not offer a transaction spanning both targets, so publication is not
transactionally atomic. Attempts and verification records remain bounded
single-process memory stores, so horizontal scaling requires a shared store.

Future-only validation remains expert review, India-English cognitive
interviews and pilot calibration, reliability/item-discrimination and
differential-item-functioning studies, representative reference distributions,
consented longitudinal outcomes, external validation, account-based history for
any high-stakes use, and Redis-backed attempt storage when scaling beyond one
replica.

## Phase boundary

No Phase 10 exists in the governing plan. Phase 9 and the Codex final review
are complete. The only release step left is a separately authorized paired
deployment from the reviewed `main` commit after merge.
