# AlterScore v3 current state

> Live handoff file. Update this document after every Luna implementation pass
> and every Codex review. Keep it short; detailed history belongs in
> `SCORING_V3_CHECKPOINTS.md`.

## Snapshot

| Field | Value |
|---|---|
| Updated | 2026-07-15 17:08:40 +05:30 |
| Branch | `codex/scoring-production-hardening` |
| HEAD before v3 phased work | `aacf2b52f6d0d6eeed6eef5d90e73a4716981793` |
| Review-start HEAD | `0c398d6d14bb3ae65360b02863d5142f4df1b043` |
| Review-start commit | `0c398d6 feat: add deterministic v3 scoring phases` |
| Active phase | Phase 5 - Frontend assessment migration |
| Luna status | Not started (Phase 5) |
| Codex review | Passed (Phase 4) |
| Overall status | Phase 4 passed after Codex security corrections; Phase 5 is the immediate next action and has not started |

## Current branch condition

- The working tree already contains substantial uncommitted scoring-hardening,
  frontend, model-artifact, test, documentation, and cleanup changes.
- These existing changes must be preserved. Luna must not reset, checkout, or
  overwrite them.
- At baseline capture, `git diff --stat` reported 76 tracked files, 4,389
  insertions, and 8,581 deletions. HEAD remained unchanged throughout Phase 0.
- At baseline capture, the untracked paths were `backend/ml/inference/text_quality.py`,
  `docs/SCORING_V3_CHECKPOINTS.md`, `docs/SCORING_V3_CURRENT_STATE.md`,
  `docs/SCORING_V3_LUNA_PLAN.md`, and
  `tests/integration/api/test_production_scoring_contract.py`.
- Later in the handoff, the untracked `docs/SCORING_V3_CODEX_REVIEW_PROMPT.md`
  was added by concurrent documentation work and was preserved. The complete
  backend test run also left the ten-file test-only bundle under
  `runtime/shared_session_trained_model_answer_only_v2/`; it was preserved and
  not promoted or copied into `models/`. The frontend build left ignored
  `frontend/dist/` output, and Python test/import runs left ignored `__pycache__`
  directories. These side effects are inventory facts, not production artifact
  promotion.
- No runtime scoring, API, question-bank, frontend source, deployment workflow,
  or checked-in model artifact was intentionally changed by Phase 0.
- The checked-in HEAD predates the uncommitted hardening work.
- Phase 1 added only the new backend-owned instrument package and its isolated
  unit test, plus this tracking update. Existing legacy scorer, schemas,
  frontend, model artifacts, deployment workflow, and prior untracked files
  remain untouched.
- Phase 2 added only the backend-owned branching package, its isolated and
  integrated unit tests, and this tracking update. Existing legacy scorer,
  schemas, frontend, model artifacts, deployment workflow, and prior
  untracked files remain untouched.
- Phase 3 added only the isolated unified scorer package, its focused tests,
  and this tracking update. It does not wire an API, change frontend behavior,
  alter the v1 scorer, regenerate model artifacts, or modify deployment.
- Phase 4 added only the secure anonymous v2 transport, bounded in-memory
  attempt/result stores, signed attempt tokens, result signing/digest logic,
  readiness/liveness routes, and Phase 4 regression tests. The legacy v1
  surface remains registered; frontend migration, cleanup, deployment, and
  model-artifact work were not started.

## Work completed before v3

- Browser/device telemetry was removed from the active scoring feature set.
- Opaque NLP/PCA serving influence was removed.
- Current frontend-shaped payloads were made acceptable to the backend.
- Text handling was changed to a small visible bounded adjustment.
- Answer-only model artifacts were regenerated as manifest v6/model 0.9.
- Frontend validation, request cancellation/timeout, and dashboard-result cache
  behavior were hardened.
- Frontend lint/build and split backend suites passed during the preceding audit.
- Unused Marquee frontend files and the unused `recharts` dependency were
  removed.

These are interim changes. The v3 plan replaces the public ML scorer with a
deterministic readiness rubric and may supersede part of this work.

## Confirmed unresolved issues driving v3

- Synthetic AUC, calibration, and fairness cannot establish real repayment
  accuracy.
- Current question and rubric weights are hand-authored and sometimes logically
  invalid.
- Unknown option IDs can pass prefix validation and fall back toward neutral.
- Frontend source exposes answer keys and scoring signals.
- Current static questions are easy to memorize or inspect.
- Current text penalty breaks score/probability consistency.
- Current explanations use a surrogate rather than faithful public-score math.
- CI/release validation, fail-closed readiness, version negotiation, browser
  privacy, and coordinated deployment need further hardening.
- Deployed production still runs an older scorer until a coordinated release.

## Locked v3 decisions

- Portfolio/educational scope only.
- India-English initial instrument.
- Primary 0-to-100 Financial Decision Readiness Index.
- Secondary illustrative 300-to-850 transformation.
- Eight parameterized objective concepts.
- Four static SJTs and two state-based branching simulations.
- Self-reported behavior and narrative remain unscored.
- Anonymous hardened attempts with immediate no-cooldown retakes using new
  forms.
- Server-only keys/rubrics, single-use attempts, signed results, and result
  verification.
- Explainability follows stable scoring/API/frontend phases.
- Synthetic XGBoost remains only as an offline Research Lab demonstration.
- Human validation and real outcomes are future scope.

## Multi-agent efficiency rule

- Luna should delegate independent audits, isolated non-overlapping file slices,
  test execution, fuzzing, accessibility, security, and dependency checks to
  lightweight subagents where parallel work materially shortens the phase.
- Luna must define shared contracts first, assign one writer per file, preserve
  one integration slot, and keep coupled/shared-contract work serial.
- Subagents cannot reset the worktree, switch branches, commit, push, deploy,
  advance phases, or update status files.
- Luna must review every subagent result, run combined tests, and record agent
  usage and verification in the phase checkpoint.
- Detailed procedure and phase-specific delegation guidance are authoritative in
  `SCORING_V3_LUNA_PLAN.md`.

## Codex review ownership

- Codex decides exactly `PASS` or `CHANGES REQUIRED`. Luna normally owns
  corrections after `CHANGES REQUIRED`; Codex may correct the reviewed phase
  only when the user explicitly authorizes it. That exception was used for the
  completed Phase 0 correction iteration 4.
- After `PASS`, Codex updates tracking and returns the next-phase handoff. A
  commit or push always requires separate explicit user authorization, so the
  worktree may remain uncommitted; an approved immediate successor may start
  from that preserved worktree after its handoff, without a commit or push.
- Luna starts the next phase only from the prompt issued after Codex's successful
  review and explicit handoff; no next phase was started here.

## Phase 0 specification freeze

These values are frozen for the v3 implementation and are not present in the
current v1 runtime yet:

| Version field | Frozen value |
|---|---|
| `contract_version` | `2.0` |
| `assessment_version` | `india-en-3.0.0` |
| `scoring_policy_version` | `readiness-rubric-1.0.0` |

The v3 public score contract returns `financial_decision_index` (0-100),
`legacy_demo_score` (illustrative 300-850), `objective_score`,
`judgment_score`, an unscored `behavior_profile`, and technical
`integrity_status`. It must not return repayment probability, synthetic
percentile, risk band, approval, eligibility, pricing, loan amount, or a claim
of creditworthiness. AlterScore remains a portfolio/educational demonstration
of demonstrated knowledge and judgment, not a lender, bureau, underwriting
tool, validated psychometric instrument, or repayment predictor. The synthetic
XGBoost system is offline Research Lab material only.

The frozen formulas are:

```text
objective_score = Fraction(100 * correct_objective_answers, 8)
static_sjt_score_internal = Fraction(100 * rubric_points, 3)
static_sjt_score_display = quantize_fraction_half_up(static_sjt_score_internal, 2)
branching_scenario_score =
    Fraction(40, 100) * obligation_coverage
    + Fraction(25, 100) * liquidity_retention
    + Fraction(20, 100) * cost_efficiency
    + Fraction(15, 100) * plan_feasibility
judgment_score = mean(four static_sjt_scores, two branching_scenario_scores)
financial_decision_index = round_fraction_half_up_to_integer(
    Fraction(55, 100) * objective_score + Fraction(45, 100) * judgment_score
)
legacy_demo_score = 300 + floor(
    Fraction(11, 2) * financial_decision_index + Fraction(1, 2)
)
```

All score-bearing inputs and monetary state use integers, and internal scoring
uses exact normalized rational arithmetic. Half-up display quantization is an
integer quotient/remainder operation, so it has no ambient Decimal context.
The judgment mean uses unrounded rational values; domain scores are quantized
to two places only for public output, and only the final index is rounded to a
whole number. Branch dimensions use positive integer server-only
`initial_liquidity` and `cost_budget` constants and these derived values:

```text
unmet = due - met
liquid_resources = cash + emergency_buffer
unencumbered_liquidity = max(0, liquid_resources - unmet)
remaining_plan_need = unmet + essentials + unfunded
obligation_coverage = 100 if due == 0 else 100 * clamp01(met / due)
liquidity_retention = 100 * clamp01(unencumbered_liquidity / initial_liquidity)
cost_efficiency = 100 * clamp01(1 - (borrowing_cost + avoidable_cost) / cost_budget)
plan_feasibility = 100 if remaining_plan_need == 0 else
    100 * clamp01((unencumbered_liquidity + confirmed_inflows)
                  / remaining_plan_need) / (1 + late_payments)
```

All monetary fields are non-negative integers at one horizon,
`0 <= required_payments_met <= required_payments_due`, and `late_payments` is a
non-negative integer. Unpaid required amounts encumber retained liquidity, so a
funded payment cannot reduce liquidity or feasibility and strictly improves
coverage until full payment. `new_borrowing` is accounted for through cash,
cost, or required-payment state exactly once. The plan freezes the complete
public component/nested schemas, canonical digest/signature encodings, exact
error-detail shapes, bounded 45-minute/10,000-entry attempt store, and redacted
24-hour/10,000-entry verification store. The single integrity vocabulary is `issued`,
`verified_attempt`, or `integrity_unavailable`; it describes technical attempt
provenance and never identity or honesty.

The frozen architecture requires eight parameterized objective concepts,
four static situational-judgment concepts, and two three-stage branching
simulations. The six-item behavior profile and optional narrative are
diagnostic/unscored and cannot affect any score. Anonymous integrity is
bounded: server-seeded new values, scenario variants, opaque presentation
IDs, randomized option order, and single-use signed attempts are required;
calculators, search, another person answering, screenshots, multiple devices,
and distributed black-box probing remain outside the guarantee. Explainability
must reconcile the formula, show objective worked solutions, show branching
state timelines and terminal dimensions, explain static SJT principles without
leaking the complete hidden rubric, link to result verification, and ground
recommendations in actual weaknesses. SHAP-style attribution and fabricated
score gains are explicitly out of scope for the v3 result.

## Current v1 contract and retirement inventory

- The active public scorer is `POST /api/score`; local debug is
  `POST /api/debug-score`. There is no current `/api/v1/score` route. The
  v1 `ScoreRequest` has a default generated `session_id`, required `answers`,
  and a default behavioral diagnostics object. Its exact nested fields, bounds,
  defaults, scenario-prefix validation, normalized 1,000-character open text,
  and recursive `extra="forbid"` behavior are recorded in the Phase 0
  checkpoint.
- The successful v1 response fields are `session_id`, `credit_score` (300-850),
  `repayment_probability` (0-1), `percentile` (0-100), SHAP-style
  `explanation`, `counterfactual_actions`, `improvement_tips`, `text_quality`,
  and `timestamp`. It remains the model-backed legacy contract and is not the
  v3 public contract.
- Current public failure behavior is: schema validation 422 with FastAPI's
  validation envelope; rate limiting 429 with `RATE_LIMITED`; unavailable
  artifacts 503 with `ARTIFACTS_NOT_READY`, raw `artifact_errors`, and possible
  resolved filesystem paths; unexpected scoring failure 500 with
  `SCORING_FAILED` and only an error-type detail; and disabled debug scoring 404 with
  `DEBUG_NOT_AVAILABLE`. The current 429/503/500 route responses use the
  `ErrorResponse` shape; the default 422 validation response does not. Failure
  logging can persist the same artifact-error details, and unauthenticated
  analytics 503 responses expose `artifact_path`. These are existing v1
  disclosure seams, not Phase 0 behavior changes.
- Runtime entrypoints are `backend/app/main.py`,
  `backend/app/api/v1/routes/score.py`, and
  `backend/app/services/scoring.py`. The active manifest is
  `models/registry/production_manifest.json` (`xgboost_monotonic_answer_only_v6`,
  model `0.9.0`) with ten declared artifact entries; parallel unsuffixed models,
  reports, text-PCA, and legacy explainers remain.
- Analytics exposes ten unauthenticated report-backed routes. FastAPI also
  exposes `/openapi.json`, `/docs`, `/docs/oauth2-redirect`, and `/redoc` by
  default. `/api/health`
  loads `models/registry/promotion_gate_policy.json` and couples health status
  to manifest artifacts plus metrics, fairness, PSI, and population-percentile
  promotion checks. The legacy scorer uses a configurable `slowapi`
  remote-address limiter and appends JSONL request logs containing request and
  session IDs, latency, artifact metadata, and legacy score/probability/
  percentile fields.
- Frontend question and result seams are `frontend/src/data/questions.js`,
  `Assessment.jsx`, `Processing.jsx`, `Results.jsx`, `Dashboard.jsx`,
  `src/lib/api.js`, and `src/utils/apiErrors.js`. The client ships 13 fixed
  questions and answer/scenario signals; result history is browser-local.
- Dependencies retain the broad FastAPI/NumPy/Pandas/SciPy/scikit-learn/XGBoost/
  LightGBM/SHAP/Torch/TabNet/spaCy/sentence-transformers/VADER/training
  surface. CI runs Python lint, frontend lint/build, pytest, reproducibility,
  and promotion-gate checks. HF deployment skips when `HF_TOKEN` is absent;
  otherwise it creates a temporary context containing `backend/`, `models/`,
  `scripts/`, `Dockerfile`, generated `.gitattributes`, and a generated README,
  then force-pushes. The
  Dockerfile's `COPY . .` and `/api/health` container healthcheck therefore
  depend on that supplied context. The scheduled keepalive masks health
  failures with `|| echo`.
- Later retire/archive seams include the v1 scorer and actual `/api/score`
  route, the XGBoost/model artifacts and research dependencies, SHAP/DiCE/NLP/
  text-PCA paths, analytics/Admin, health/promotion coupling, the rate limiter
  and JSONL logger, raw artifact/path errors, default docs/OpenAPI exposure,
  fallback artifact loaders, legacy parsers, deployment and keepalive behavior,
  governance scripts, runtime bundles, and every concrete legacy documentation
  path. The path- and field-complete inventory is in Phase 0 correction
  iteration 4 of `SCORING_V3_CHECKPOINTS.md`.

## Phase 0 baseline evidence

- Frontend: `npm.cmd run lint` passed; `npm.cmd run build` passed with Vite
  8.0.16 and 1,839 modules transformed.
- Backend: `ALTERSCORE_ENV=test` with the existing Python 3.12.7 environment
  ran the complete suite: 225 passed, one `PytestCacheWarning`, 110.65s.
- Hygiene: `git diff --check` passed. Line-ending normalization warnings and
  the local global-ignore permission warning were recorded in the checkpoint.
- The baseline inventory confirms the current v1 public route is `POST
  /api/score`, backed by the XGBoost monotonic artifact manifest, static
  client-shipped questions/answer keys, SHAP/DiCE explanations, analytics
  artifact routes, local browser result caching, and the existing GitHub
  Actions/Hugging Face deployment workflow. These are later migration or
  retirement seams, not Phase 0 changes.

## Phase 1 implementation handoff

Phase 1 is implemented and passed Codex review. The new
`backend.app.instrument` package is the v3 canonical instrument authority for
this phase and is independent of the v1 scorer, XGBoost features, persisted
artifacts, frontend question data, and API routes.

- Eight deterministic seeded objective generators cover cash-flow arithmetic,
  simple interest, borrowing-cost comparison, percentage discount, inflation,
  due-date shortfall, total repayment, and emergency-buffer coverage.
- Four static SJTs use the four frozen concepts and private exact `0..3`
  rubrics. Their public options contain only IDs and labels.
- Six behavior-profile items expose exactly the frozen labels `Never`, `Rarely`,
  `Sometimes`, `Often`, `Always`, and `Not applicable`; behavior and the
  optional 1,000-character narrative are unscored.
- Exact `Fraction` objective/SJT calculations, strict integer/range checks,
  canonical item/option rejection, deterministic sub-seeding, and fail-closed
  definition integrity checks are implemented. Public narrative length is the
  frozen literal `1000`, and cross-category presentation-ID collisions fail
  closed before an ambiguous form can be issued.
- Public serialization is an explicit allowlist and omits keys, bounds,
  generation rules, weights, rubrics, rationales, issued values, and seed.
- No API endpoint, branching simulation, frontend behavior, v1 scorer, model
  artifact, deployment workflow, or Phase 2 code was added or changed.

### Phase 1 verification

- Codex target tests: `.venv312\Scripts\python.exe -B -m pytest -o "addopts="
  -p no:cacheprovider --basetemp C:\tmp\alterscore-phase1-final-target-20260715
  --tb=short -q tests\unit\backend\test_instrument.py` passed 20 tests in
  1.68 seconds. Pytest emitted one `PytestConfigWarning` because disabling the
  cache provider leaves the repository `cache_dir` option unrecognized.
- Codex non-ML backend units: the same isolated options against
  `tests\unit\backend` passed 49 tests in 1.97 seconds.
- Static check: `.venv312\Scripts\ruff.exe check backend\app\instrument
  tests\unit\backend\test_instrument.py` passed with `All checks passed!`.
- Existing Phase 0 frontend/backend baselines remain the recorded evidence;
  they were not rerun because Phase 1 does not change frontend or legacy v1
  runtime behavior.

## Phase 2 review handoff

Phase 2 passed Codex review. The new
`backend.app.branching` package is a pure, deterministic, backend-owned
financial-state engine. It is not imported by the v1 API scorer, frontend,
analytics, deployment workflow, or model-artifact loader.

- The shared frozen state has the eleven canonical fields from the plan. State
  endpoints are immutable and validated; cumulative obligations, payments,
  borrowing, costs, and lateness cannot be decreased. Linked payments enforce
  the frozen conservation and non-worsening clauses with no bypass flag.
- The two simulations are `branching_emi_supplier_opportunity` and
  `forecast_shortfall_counterparty_negotiation`. Each has three stages and
  exactly three options per stage, yielding 27 reachable paths each and 54
  complete paths total.
- Each option is a pure state transition. The terminal result contains the
  complete structured three-stage evidence timeline, terminal state, four
  exact `Fraction` dimensions, and the frozen weighted score. There are no
  stage scores, path bonuses, hand-authored totals, network calls, or frontend
  integration.
- Path enumeration canonicalizes option order. The tests cover independent
  formula recomputation, clamping and zero denominators, all 54 paths,
  replay determinism, linked-payment monotonicity, rejection clauses,
  identical-terminal-state equality, stage-position neutrality, and the
  absence of a new-borrowing-principal score bonus.

### Codex Phase 2 review corrections and verification

- Borrowing now fails closed unless it is economically reflected in cash,
  borrowing cost, or required-payment state; standalone principal cannot be
  introduced by a malformed option transition.
- Definition metadata and child objects are strict and fail closed at both
  construction and execution. A tampered frozen definition is rejected before
  any path can run.
- The counterparty simulation now records actual collection actions rather
  than self-reported forecasts. Its final stage applies an all-cash or
  good-faith payment arrangement, or records a priced extension, so the
  central required-payment state is reconciled along terminal routes.
- Codex focused target after correction: **37 passed in 0.60 s**; complete
  backend units: **86 passed in 2.00 s**; Ruff: **All checks passed**.
  An independent exact oracle/property probe passed all 54 paths and 3,150
  linked-payment monotonicity checks. `git diff --check` passed; each
  untracked Phase 2 file also passed a no-index whitespace check.

### Phase 2 implementation verification (Luna historical record)

- Focused Phase 2 target: `.venv312\Scripts\python.exe -B -m pytest -o
  "addopts=" -p no:cacheprovider --basetemp
  C:\tmp\alterscore-phase2-target-20260715 --tb=short -q
  tests\unit\backend\test_branching_model.py
  tests\unit\backend\test_branching_emi.py
  tests\unit\backend\test_branching_negotiation.py
  tests\unit\backend\test_branching_phase2.py` — **34 passed in 0.39 s**;
  one expected `PytestConfigWarning` for the disabled cache provider.
- Complete backend unit suite: `.venv312\Scripts\python.exe -B -m pytest -o
  "addopts=" -p no:cacheprovider --basetemp
  C:\tmp\alterscore-phase2-backend-20260715 --tb=short -q
  tests\unit\backend` — **83 passed in 2.37 s**; one expected
  `PytestConfigWarning` for the disabled cache provider.
- Static check: `.venv312\Scripts\ruff.exe check backend\app\branching
  tests\unit\backend\test_branching_model.py
  tests\unit\backend\test_branching_emi.py
  tests\unit\backend\test_branching_negotiation.py
  tests\unit\backend\test_branching_phase2.py` — **All checks passed!**
- The repository `.venv312` interpreter initially terminated before test
  collection with Windows status `-1073741790`, including for a trivial
  `-c` command. The exact pytest checks above were rerun successfully through
  the approved elevated execution path; no dependency installation occurred.

### Phase 2 limitations and next boundary

No API route, attempt/result storage, anonymous transport, final unified
scorer, frontend question migration, explainability response, v1 retirement,
deployment change, model-artifact regeneration, commit, or push was performed.
The canonical transition validator currently treats a decrease in required
obligations as invalid because explicit obligation cancellation is not a
frozen Phase 2 transition. Phase 3 later completed and passed Codex review.

## Phase 3 review handoff

Phase 3 passed Codex review. The new
`backend.app.unified_scoring` package is a pure deterministic composition of
the Phase 1 canonical instrument and Phase 2 branching engine. It is isolated
from the current API, v1 scorer, ML/artifact loaders, frontend, deployment
workflow, signing, attempt tokens, and result transport.

- The scorer accepts exactly 18 scored responses: eight objective items, four
  static SJTs, and six branching stage choices. The six behavior-profile items
  and optional narrative are shape-validated, returned as an unscored profile,
  and excluded from every score and recommendation decision.
- Objective scoring remains exact: correct answers are averaged over the eight
  objective items. Judgment is the equal-weight mean of the four static-SJT
  scores and two terminal branching scores. The final index is the exact
  half-up rounding of `0.55 * objective_score + 0.45 * judgment_score`, and
  the illustrative legacy value is the exact frozen 300-to-850 transformation.
  Internal calculations use `Fraction`; `Decimal2` is applied only to the
  explanation display fields.
- The unsigned `Explanation` contains formula reconciliation, all eight
  objective issued values and worked calculations, four principle-level static
  SJT explanations, two three-stage branching replays with state deltas and
  terminal dimensions, deterministic recommendations, and the frozen
  limitations. It does not expose option IDs, rubric points, private rationales,
  SHAP/probability fields, signing material, or transport metadata.
- Branching recommendations use the explicit deterministic predicate
  `scenario_score < 60`. If dimensions tie, the weakest dimension is selected
  in the canonical `TerminalDimensions.as_dict()` order:
  `obligation_coverage`, `liquidity_retention`, `cost_efficiency`,
  `plan_feasibility`. Objective evidence is emitted in canonical item order,
  then branching evidence in scenario order; a maintenance recommendation is
  emitted only when no weakness evidence exists.
- Frozen versions remain `contract_version: 2.0`,
  `assessment_version: india-en-3.0.0`, and
  `scoring_policy_version: readiness-rubric-1.0.0`.

### Codex Phase 3 review corrections and verification

- Formula display values, exact objective/judgment contributions, and their
  exact weighted total now reconcile at the `UnifiedScoreResult` boundary.
  Forged nested Pydantic copies fail closed before a later phase can consume
  inconsistent unsigned evidence.
- `Decimal2` serialization is explicitly JSON-numeric rather than Pydantic's
  default Decimal string encoding. The Phase 4 response/digest boundary will
  therefore receive the frozen JSON number type.
- The stale current-state claim that Phase 4 tampering tests already existed
  was corrected. Phase 4 remains unimplemented.
- Codex focused target after correction: **140 passed in 1.23 s**; complete
  backend units: **226 passed in 3.06 s**; Ruff: **All checks passed**. An
  independent probe reconciled all 729 pairs of two-scenario branch paths,
  confirmed numeric Decimal2 JSON, and rejected a forged formula.

### Phase 3 implementation verification (Luna historical record)

- Focused Phase 3 target: **139 passed in 1.35 s**.
- Full backend unit suite: **225 passed in 3.25 s**.
- Ruff on the new package and Phase 3 tests: **All checks passed!**
- AST import-boundary audit: **PASS**; no API, ML, v1, network, or transport
  imports occur in the isolated scorer package.
- `git diff --check`: **PASS** with the preserved worktree's existing
  line-ending and global-ignore permission warnings only.
- Every verification command used the existing `.venv312` environment through
  the approved elevated execution path; no dependency installation or model
  artifact generation occurred.

### Phase 3 limitations and next boundary

Phase 3 is not wired to an API, anonymous attempt store, signing/digest
serializer, frontend question bank, analytics route, v1 retirement path,
deployment workflow, or model-artifact pipeline. The branching weakness
threshold is an internal deterministic Phase 3 recommendation rule and is not
an underwriting or creditworthiness claim. Phase 4 is approved to begin but
has now been implemented and handed to Codex for review below.

## Phase 4 implementation and Codex review

Phase 4 is complete and passed Codex review. The implementation is isolated
under `backend/app/api/v2/` and preserves the v1 API, frontend source,
deployment workflows, model artifacts, and legacy files.

- The frozen versions remain `contract_version: 2.0`,
  `assessment_version: india-en-3.0.0`, and
  `scoring_policy_version: readiness-rubric-1.0.0`.
- `GET /api/v2/assessment/form` issues exactly eight objective, four static
  SJT, six branching, and six behavior items with per-attempt numeric values,
  opaque IDs, randomized options, a 2,700-second expiry, and no answer keys,
  rubrics, generation bounds, seeds, or private rationales.
- `POST /api/v2/assessment/score` accepts only the frozen version fields,
  issued public IDs, strict integer/choice values, behavior selections, and a
  bounded optional narrative. Duplicate JSON keys are rejected before schema
  validation; bearer tokens are signed, domain-separated, single-use, and
  never stored raw.
- Results use the Phase 3 exact formulas, public-ID-remapped explanations,
  SHA-256 JCS-compatible explanation digests, HMAC-SHA256 signatures, a
  24-hour bounded redacted verification store, and no raw answer/narrative,
  behavior, option timeline, rubric, or token data in verification records.
- `/api/live` is process liveness only. `/api/ready` reports the six frozen
  checks in order and returns HTTP 503 when signing configuration is missing.
  v2/live/ready responses set `Cache-Control: no-store` and
  `Referrer-Policy: no-referrer`; form and score limits use bounded salted
  network-hash state.
- Verification and replay/tampering failures are explicit and privacy-safe;
  no unsigned result summary is returned. Legacy ML startup degradation does
  not prevent v2 liveness/readiness from serving structured responses.
- Codex corrected the review findings before approval: assessment token issuance
  and scoring now fail closed on plaintext transport; v2 access-log client
  scope is redacted after retaining only a temporary input for salted rate
  limiting; signing readiness requires a base64url encoding of at least 32
  sufficiently diverse bytes; and deeply nested JSON is rejected before it
  can escape as an internal error.

### Codex Phase 4 verification

- Focused adversarial API suite: **17 passed in 7.48 s**.
- Combined backend-unit and API-integration regression: **284 passed in
  16.01 s**.
- Ruff on the Phase 4 API, app integration, settings, and tests: **All checks
  passed**.
- `git diff --check`: **PASS** with only preserved line-ending and
  global-ignore permission warnings.

### Phase 4 limitations and next boundary

The in-memory attempt and verification stores intentionally lose state on
process restart and keep no durable or user-indexed history. Deployment must
supply a securely generated `secrets.token_urlsafe(32)`-equivalent signing
secret and establish the trusted HTTPS ASGI scheme before v2 becomes ready.
Phase 4 does not migrate the frontend, retire/archive legacy files, change
analytics behavior, modify deployment workflows, or regenerate model artifacts.

## Immediate next action

Luna may implement Phase 5 frontend assessment migration only, then stop at
`READY FOR REVIEW`; do not begin Phase 6.

## Blockers

None for Phase 5 implementation. Production readiness remains fail-closed
until deployment supplies the required signing secret and trusted HTTPS ASGI
scheme. All unrelated dirty-worktree paths remain preserved and unstaged.

## Historical verification evidence before Phase 4

Codex re-review iteration 6 independently verified:

- frontend lint: PASS, exit 0;
- isolated frontend production build: PASS, Vite 8.0.16, 1,839 modules,
  1.80s;
- complete backend suite: 225 passed in 144.04s with pytest cache and trained
  session artifacts redirected to `C:\tmp`;
- `git diff --check`: PASS with existing line-ending warnings;
- branch/HEAD/staged state and the 76-path tracked baseline diff remain
  unchanged; no Phase 1 runtime symbols were found;
- frozen-contract consistency scan: PASS; the frozen Phase 4 plan requires
  attempt-token, result-record, signature, and explanation-digest tampering
  coverage without a result token. Those tests and the Phase 4 implementation
  have not started, and the live handoff consistently permits only the approved
  immediate successor from the preserved uncommitted worktree;
- Phase 1 review: 10,000-seed deterministic/secrecy probe passed; focused
  target tests passed 20 tests; non-ML backend units passed 49 tests; Ruff and
  `git diff --check` passed.
- Phase 1 fixes: public `NarrativeConfig.max_length` is frozen to literal 1000,
  and catalog integrity rejects cross-category presentation-ID collisions.
- review decision: `PASS` for Phase 1; Phase 2 handoff follows this historical
  evidence section.

## Latest Phase 4 verification evidence

- Initial Luna claims were independently re-tested rather than accepted.
- Codex focused Phase 4 adversarial API suite: **17 passed in 7.48 s**.
- Codex combined backend-unit and API-integration suite: **284 passed in
  16.01 s**.
- Codex Phase 4 Ruff check: **All checks passed!**
- `git diff --check`: **PASS**; only preserved LF/CRLF normalization and
  inaccessible global-ignore warnings were emitted.
- The review started from `0c398d6d14bb3ae65360b02863d5142f4df1b043`; all
  pre-existing tracked and untracked changes were preserved.
- Phase 5 has not started; it is now the approved immediate next action.

## Update template

```markdown
## Snapshot

| Field | Value |
|---|---|
| Updated | YYYY-MM-DD HH:MM timezone |
| Branch | branch |
| HEAD | sha |
| Active phase | phase |
| Luna status | Not started / In progress / Complete |
| Codex review | Pending / Changes required / Passed |
| Overall status | concise status |

## Immediate next action

One concrete next action only.

## Blockers

List blockers or `None`.
```
