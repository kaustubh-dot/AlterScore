# AlterScore v3 Luna 5.6 implementation plan

> **Historical plan note (2026-07-17):** the original frozen
> `readiness-rubric-1.0.0` contract was superseded after exhaustive audit and
> explicit policy approval. The implemented production candidate uses exact
> feasible-range branch normalization under `readiness-rubric-1.1.0`; see
> `SCORING_V3_EXHAUSTIVE_CERTIFICATION_2026-07-17.md`.

## Purpose

This document is the decision-complete implementation plan for replacing the
public AlterScore scorer with an anonymous-hardened, deterministic Financial
Decision Readiness assessment.

AlterScore remains a personal resume/portfolio project. The public score must
not claim to predict repayment, establish creditworthiness, replace a credit
bureau, approve a loan, or represent a human-validated psychometric instrument.
The existing synthetic XGBoost work will remain only as a clearly separated
offline research demonstration.

All work must remain on `codex/scoring-production-hardening`.

## Phase and review protocol

Luna implements exactly one phase and then stops. Codex reviews that phase
before Luna starts the next one.

For each handoff, Luna must report:

- files added, changed, deleted, or archived;
- behavior and public-interface changes;
- tests added and exact commands/results;
- known limitations;
- `git diff --check` result;
- confirmation that no later-phase work was included.

Codex will inspect the full diff, run independent checks, and probe adversarial
cases. The review decision is exactly `PASS` or `CHANGES REQUIRED`. After
`CHANGES REQUIRED`, Luna normally corrects the same phase and stops for another
review. Codex may implement corrections only when the user explicitly
authorizes Codex to do so; that authorization does not permit the next phase,
git-state changes, deployment, or any other out-of-scope action.

After the phase passes, Codex updates both tracking documents and returns the
handoff for exactly the next phase. Staging, committing, and pushing remain
separate operations that require explicit user authorization; without that
authorization the worktree stays uncommitted. An approved immediate next phase
may nevertheless start from that preserved worktree after Codex updates tracking
and issues its handoff; commit or push is not a prerequisite. Codex then returns
a ready-to-paste prompt for Luna to implement exactly the next phase. Luna never
starts the next phase before that prompt is issued.

## Multi-agent execution rules

Luna is the phase owner and integration authority. Luna should use lightweight
subagents when two or more tasks are genuinely independent and parallel work
will shorten the phase without weakening correctness.

### Appropriate delegation

Prefer subagents for:

- read-only audits and reference tracing;
- independent frontend and backend inventories;
- isolated implementation slices with non-overlapping file ownership;
- generator fuzzing, exhaustive-path checks, contract probes, and bundle scans;
- accessibility, security, dependency, documentation, and stale-reference
  audits;
- independent verification of another agent's implementation.

Do not spawn a subagent for a small sequential task Luna can finish faster.
Do not delegate a decision that is already frozen in this plan.

### Required procedure

1. Luna first defines the phase's shared contracts, invariants, file boundaries,
   and integration order.
2. Every subagent receives a bounded task containing scope, allowed files,
   forbidden actions, expected output, required tests, and a stop condition.
3. Use the cheapest/lightest capable subagent model for inventories, searches,
   test execution, documentation checks, and other mechanical work. Reserve
   stronger reasoning for scoring, state-transition, security, and contract
   decisions.
4. Assign exactly one writer per file. Agents may read shared files, but two
   agents must never edit the same file concurrently.
5. Shared schemas, version constants, public API contracts, scoring formulas,
   tracking documents, and git operations remain owned by Luna unless Luna
   explicitly serializes their ownership.
6. No subagent may reset/clean the worktree, switch branches, commit, push,
   deploy, start a later phase, or modify phase status.
7. Luna collects every result, reviews its diff/evidence, rejects unsupported
   conclusions, resolves integration conflicts, and runs the combined phase
   suite after all subagent work is merged.
8. A subagent's claim is not completion evidence until Luna independently
   verifies it. A second read-only reviewer is preferred for scoring, security,
   branch-exhaustiveness, and public-contract changes.
9. If work is coupled, overlapping, or blocked on a shared decision, Luna must
   perform it serially rather than forcing parallelism.
10. Luna is solely responsible for updating `SCORING_V3_CURRENT_STATE.md` and
    appending the implementation checkpoint.

### Concurrency guidance by phase

- Phase 0: parallel read-only frontend, backend, and release/inventory audits.
- Phase 1: separate objective-generation, instrument-serialization, and
  adversarial-test slices after the canonical schema is fixed.
- Phase 2: one isolated implementation slice per branching simulation plus an
  independent property-test auditor; Luna owns the shared state model.
- Phase 3: Luna owns score composition; delegate invariant/persona tests and
  independent formula reconciliation.
- Phase 4: separate attempt lifecycle, result signing/verification, and
  adversarial API tests only after Luna freezes the API contract.
- Phase 5: separate assessment UI, accessibility/error-flow tests, and bundle
  secrecy audit with non-overlapping files.
- Phase 6: separate objective worked solutions, branching replay, and visual/
  accessibility checks; Luna owns the explanation response contract.
- Phase 7: parallel read-only import, artifact, dependency, and stale-doc audits
  before Luna performs removals serially.
- Phase 8: separate CI, runtime readiness, and release/rollback reviews.
- Phase 9: use independent scoring, security, frontend, and release auditors,
  then reconcile all findings before final handoff.

Keep active agent count within the available concurrency limit and leave Luna a
slot for integration. Parallel speed is useful only when ownership is clear.

## Final scoring policy

### Public outputs

- `financial_decision_index`: canonical score from 0 to 100.
- `legacy_demo_score`: secondary illustrative 300-to-850 transformation.
- `objective_score`: financial knowledge score.
- `judgment_score`: financial decision-knowledge score.
- `behavior_profile`: unscored self-reflection.
- `integrity_status`: technical provenance of the anonymous attempt.

The scorer must not return repayment probability, synthetic percentile, risk
band, approval, eligibility, pricing, or a loan amount.

### Frozen public contract schemas

All schema objects use `extra="forbid"`. Timestamps are required ISO-8601 UTC
strings with a `Z` suffix and second precision. Opaque IDs are non-empty,
server-generated strings with at least 128 bits of randomness. The bearer
`attempt_token` is a separate secret. `Decimal2` below means a JSON number in
`0..100` rounded half-up to two decimal places; JSON does not preserve trailing
zeroes, so clients display two fractional digits rather than depending on the
wire lexeme.

Every v2 success, liveness, and readiness response contains `PublicMetadata`:
`contract_version="2.0"`, `assessment_version="india-en-3.0.0"`,
`scoring_policy_version="readiness-rubric-1.0.0"`, opaque `request_id`, and
public `release_sha`, all required strings. Error responses contain the three
version literals and place `request_id` inside `error`; they do not duplicate it
at top level.

The reusable public component schemas are:

- `OptionPresentation`: exactly `{option_id: string, label: string}`.
- `ObjectivePresentation`: exactly `{presentation_id: string,
  item_type: "objective", prompt: string, response_kind: "integer",
  required: true}`. Generation bounds, key, seed, and rationale remain
  server-only.
- `StaticSjtPresentation`: exactly `{presentation_id: string,
  item_type: "static_sjt", prompt: string, response_kind: "single_choice",
  required: true, options: OptionPresentation[4]}`.
- `BranchingPresentation`: exactly `{presentation_id: string,
  item_type: "branching", scenario_presentation_id: string, stage_index:
  integer 1..3, prompt: string, response_kind: "single_choice", required: true,
  options: OptionPresentation[3]}`. The six stage prompts are issued up front;
  stage two and three are displayed sequentially but their wording is
  path-independent. The selected sequence drives the server-only state
  transitions. Options are independently shuffled within each stage.
- `BehaviorProfilePresentation`: exactly `{presentation_id: string,
  item_type: "behavior_profile", prompt: string,
  response_kind: "single_choice", required: true,
  options: OptionPresentation[6]}`. Its labels are exactly `Never`, `Rarely`,
  `Sometimes`, `Often`, `Always`, and `Not applicable`, in randomized order.
- `NarrativeConfig`: exactly `{enabled: boolean, prompt: string,
  max_length: 1000}`.

`FormResponse` for `GET /api/v2/assessment/form` contains `PublicMetadata` plus
required `attempt_id`, secret `attempt_token`, `issued_at`, `expires_at`,
`integrity_status="issued"`, `items`, `behavior_profile_items`, and `narrative`.
`items` contains exactly eight `ObjectivePresentation`, four
`StaticSjtPresentation`, and six `BranchingPresentation` objects.
`behavior_profile_items` contains exactly six `BehaviorProfilePresentation`
objects. No response field contains answer keys, rubric points, transition
deltas, generation rules/bounds, seed, or hidden rationale.

`ScoreSubmission` for `POST /api/v2/assessment/score` transports
`Authorization: Bearer <attempt_token>` only over HTTPS. The token, attempt ID,
and any client-selected identifier are forbidden in JSON. The body contains
exactly the three version fields, `responses`, `behavior_profile`, and optional
`narrative`. `responses` is an object with exactly the 18 issued scored
`presentation_id` keys; objective values are JSON integers and choice values
are issued `option_id` strings. `behavior_profile` is an object with exactly the
six issued behavior `presentation_id` keys and issued behavior `option_id`
strings. `narrative` is omitted, `null`, or a string of at most 1,000 Unicode
characters. Raw JSON parsing rejects duplicate keys before schema validation.
Missing, extra, cross-attempt, unknown, duplicate, or wrong-type values fail.

The detailed `Explanation` schema is exactly:

- `formula`: `{objective_score: Decimal2, judgment_score: Decimal2,
  objective_weight: "0.55", judgment_weight: "0.45",
  objective_contribution_exact: fraction-string,
  judgment_contribution_exact: fraction-string,
  weighted_total_exact: fraction-string, financial_decision_index: integer
  0..100, legacy_demo_score: integer 300..850}`. A fraction string is two
  coprime base-10 integers separated by `/` with a positive denominator.
- `objective_items`: exactly eight objects
  `{presentation_id, concept, issued_values, submitted_answer, correct_answer,
  is_correct, worked_calculation, concept_explanation}`. `issued_values` is an
  ordered array of one or more `{name: string, value: integer, unit: string}`;
  answers are integers, `is_correct` is boolean, and the remaining fields are
  non-empty strings.
- `static_sjt_items`: exactly four objects
  `{presentation_id, selected_option_label, principle, protects, risks,
  stronger_principle}`, all non-empty strings. They contain no option IDs,
  points, option-to-point table, or complete hidden rubric.
- `branching_scenarios`: exactly two objects
  `{scenario_presentation_id, starting_state, timeline, terminal_state,
  dimensions, scenario_score}`. `timeline` contains exactly three ordered
  objects `{stage_index, presentation_id, selected_option_label, state_before,
  state_delta, state_after}`. State objects use all eleven canonical state
  fields; terminal/state values are integers and deltas are integers.
  `dimensions` is exactly `{obligation_coverage: Decimal2,
  liquidity_retention: Decimal2, cost_efficiency: Decimal2,
  plan_feasibility: Decimal2}` and `scenario_score` is `Decimal2`.
- `recommendations`: an array of zero or more objects
  `{recommendation: string, evidence_type: "objective"|"branching"|"maintenance",
  evidence_ids: string[]}`. Non-maintenance recommendations require at least
  one actual missed-objective presentation ID or weak branching-scenario ID;
  maintenance guidance uses an empty evidence array.

`ScoreResponse` contains `PublicMetadata` plus required `result_id`,
`attempt_id`, `issued_at`, `expires_at`,
`integrity_status="verified_attempt"`, `financial_decision_index` (integer
0..100), `legacy_demo_score` (integer 300..850), `objective_score` and
`judgment_score` (`Decimal2`), `behavior_profile`, `limitations`,
`result_signature`, `explanation_digest`, and `explanation` (`Explanation`).
`behavior_profile` is an array of exactly six
`{presentation_id: string, selected_value: behavior-label}` objects.
`limitations` is a non-empty array of unique non-empty strings.
For this response, `issued_at` is the result-signing time and `expires_at` is
exactly 24 hours later; they are distinct from the form's attempt timestamps.
`explanation_digest` is `sha256:` followed by 64 lowercase hexadecimal digits
over the UTF-8 RFC 8785 JSON Canonicalization Scheme representation of the
`Explanation` object. `result_signature` is `hmac-sha256-v1:` followed by
unpadded base64url HMAC-SHA256 of the canonical signing projection using the
server secret.

The signing projection contains exactly the three version fields, `release_sha`,
`result_id`, `attempt_id`, `issued_at`, `expires_at`, `integrity_status`, all
four numeric score values, `limitations`, and `explanation_digest`; it excludes
`request_id`, `result_signature`, behavior values, and the detailed
explanation. Before canonicalization, the two `Decimal2` scores are represented
in the signing projection as integer hundredths so equivalent JSON number
spellings cannot change the signature.

`VerificationResponse` contains `PublicMetadata` plus the exact signed
projection fields and `result_signature`. It contains no `explanation`,
behavior profile, raw response, narrative, option-selection timeline, or hidden
rubric. `result_id` is the only URL identifier; no bearer or result token is in
the URL.

`LiveResponse` contains `PublicMetadata`, `status="ok"`, and `timestamp`; it
checks process liveness only. `ReadyResponse` contains `PublicMetadata`,
`status` in `ready|degraded|not_ready`, `timestamp`, and `checks`. `checks` is an
array of exactly six `{name, status, message}` objects for `instrument`,
`scorer`, `signing`, `attempt_store`, `verification_store`, and `rate_limits`;
`status` is `pass|warn|fail`, and messages are allow-listed and secret-free.

`ErrorResponse` is exactly `{contract_version, assessment_version,
scoring_policy_version, error: {code, message, details, request_id,
timestamp}}`. `code` is one of `malformed_request`, `unsupported_version`,
`attempt_expired`, `attempt_consumed`, `attempt_stale`, `unknown_option`,
`invalid_response`, `form_unavailable`, `result_not_found`,
`integrity_failed`, `rate_limited`, `not_ready`, or `internal_error`.
`details` is exactly one of these allow-listed shapes:

- `malformed_request`, `invalid_response`, or `unknown_option`:
  `{fields: string[]}` containing field names only;
- `unsupported_version`: `{supported_contract_version,
  supported_assessment_version, supported_scoring_policy_version}`;
- attempt expiry/consumed/stale: `{retryable: true, new_form_required: true}`;
- `rate_limited`: `{retry_after_seconds: integer >= 1}`;
- `not_ready` or `form_unavailable`: `{failed_checks: string[]}` using stable
  check names only;
- `result_not_found`, `integrity_failed`, and `internal_error`: `{}`.

Invalid input uses 400/422, missing or expired/evicted results use 404,
consumed/replayed attempts use 409, rate limits use 429, unavailable/not-ready
uses 503, and unexpected failures use a generic 500. No error includes secrets,
raw values/answers, narrative, IP addresses, traceback text, exception text,
artifact paths, or report payloads.

The canonical integrity vocabulary is `integrity_status` with only
`issued`, `verified_attempt`, and `integrity_unavailable`. `verified_attempt`
means that the server issued the form, validated its unexpired single-use
mapping, consumed it atomically, and signed the result; it never means that a
person's identity, honesty, or real-world behaviour was verified.

The successful score response is the only response that carries the detailed
explanation. The frontend may retain it in `sessionStorage` for at most 24
hours; it must not use `localStorage` or persistent attempt-token storage. The
server keeps no durable or user-indexed result history. It keeps only the exact
redacted `VerificationResponse` record in a bounded in-memory verification
store with `RESULT_TTL_SECONDS=86400` and `RESULT_STORE_MAX_ENTRIES=10000`.
`expires_at` is exactly `issued_at + 24 hours`. Expired and capacity-evicted
records are removed and return 404 `result_not_found`; a process restart may
also make a record unavailable and returns the same privacy-preserving error.
Every lookup, expiry sweep, and insertion is serialized under the store lock.
Before insertion the store removes expired records; if it is still at capacity,
it evicts the record with the earliest `(expires_at, issued_at, result_id)` tuple.
The store contains no explanation, behavior values, narrative, raw answers,
option timeline, token, IP/device data, or hidden rubric. The complete score
response is never written to request logs. A fresh browser can restore only the
redacted summary while that bounded record survives; full worked evidence is
available only from the score response retained in the original browser
session.

### Formula

```text
objective_score =
    Fraction(100 * correct_objective_answers, 8)

static_sjt_score_internal =
    Fraction(100 * rubric_points, 3)

static_sjt_score_display =
    quantize_fraction_half_up(static_sjt_score_internal, 2)

branching_scenario_score =
    Fraction(40, 100) * obligation_coverage
    + Fraction(25, 100) * liquidity_retention
    + Fraction(20, 100) * cost_efficiency
    + Fraction(15, 100) * plan_feasibility

judgment_score =
    mean(
        four static_sjt_scores,
        two branching_scenario_scores
    )

financial_decision_index =
    round_fraction_half_up_to_integer(
        Fraction(55, 100) * objective_score
        + Fraction(45, 100) * judgment_score
    )

legacy_demo_score =
    300 + floor(Fraction(11, 2) * financial_decision_index + Fraction(1, 2))
```

All objective answers, rubric points, monetary state values, counters, and
server-only scenario constants are integers. Internal scoring uses normalized
exact rational numbers (`fractions.Fraction` semantics), never binary floats or
finite Decimal division. `rubric_points` is an integer from 0 through 3. The
judgment mean uses the unrounded rational static and branching scores.

For a non-negative fraction `n/d`, half-up quantization to `p` decimal places is
defined without a Decimal context: set `scale=10**p`, compute
`q,r=divmod(n*scale,d)`, and return `(q + 1 if 2*r >= d else q) / scale`.
Whole-number half-up rounding uses the same rule with `p=0`. Public domain
scores are numeric values quantized to two places, so static displays are
`0.00`, `33.33`, `66.67`, and `100.00`; clients render two fractional digits.
No displayed/quantized value is fed back into scoring. Only the final weighted
index is rounded to an integer, and `legacy_demo_score` is derived from that
integer.

All eight objective concepts and all six judgment scenarios are required. No
neutral-value imputation is allowed. Each judgment scenario has equal weight,
regardless of branch depth. Behavior questions and narrative text never affect
the score.

## Question architecture

### Eight parameterized objective concepts

1. Cash-flow arithmetic.
2. Simple interest.
3. Borrowing-cost comparison.
4. Percentage discount.
5. Inflation and purchasing power.
6. Due-date shortfall.
7. Total borrowing cost.
8. Emergency-buffer coverage.

Each attempt receives new server-generated values. Generation must be
deterministic from a server seed, use documented safe parameter ranges, yield
one exact answer, and reject ambiguous, tied, negative, fractional, or invalid
forms. Exact answers are required unless the prompt explicitly asks for
rounding.

### Four static situational-judgment concepts

Use one selected action and a server-only 0-to-3 rubric. Every option must be
plausible, and every prompt must contain enough quantitative facts for a
defensible answer.

1. Overdue receivable and upcoming required expense.
2. Windfall, high-cost overdue debt, and no emergency buffer.
3. Loss-making product with a fixed cash runway.
4. Comparing loan total cost, fees, and cash-flow timing.

Static rubric scores use the exact internal formula above and serialize as
`0.00`, `33.33`, `66.67`, or `100.00`.

### Two branching simulations

Each simulation has three stages, three plausible choices per stage, and at
most 27 complete paths. Outcomes are deterministic. The final scenario score
is derived from terminal financial state rather than manually authored path
points.

1. EMI, essential expenses, and a supplier opportunity.
2. Forecast payment shortfall and counterparty negotiation.

Canonical state may contain only financially interpretable fields:

```text
cash_available
required_payments_due
required_payments_met
confirmed_inflows
essential_expenses
emergency_buffer
new_borrowing
borrowing_cost
avoidable_cost
late_payments
unfunded_commitments
```

Required invariants:

- missing a required payment cannot improve the score;
- increasing avoidable cost cannot improve the score;
- increasing an unfunded commitment cannot improve feasibility;
- preserving additional cash cannot reduce liquidity, all else equal;
- a dominated action cannot outperform its dominating action;
- identical terminal states receive identical scores;
- branch depth cannot increase scenario weight;
- display order cannot affect results.

For exact branching arithmetic, each simulation supplies two positive integer,
server-only constants: `initial_liquidity` and `cost_budget`. They are scenario
parameters, not additional public state fields. Every monetary state field is
a non-negative integer in one scenario unit and one horizon. `late_payments` is
a non-negative integer count. `required_payments_met <=
required_payments_due`. `cash_available` excludes confirmed inflows not yet
received and excludes the separately tracked emergency buffer.
`new_borrowing` is a source amount already reflected in cash, borrowing cost,
or required-payment state; it is never charged again as a standalone score
term.

The following values are derived, not additional canonical state fields:

```text
unmet_required_payments = required_payments_due - required_payments_met
liquid_resources = cash_available + emergency_buffer
unencumbered_liquidity = max(0, liquid_resources - unmet_required_payments)
remaining_plan_need =
    unmet_required_payments + essential_expenses + unfunded_commitments
```

Unpaid required amounts therefore encumber retained liquid resources before
liquidity or feasibility receives credit. Define
`clamp01(x)=min(Fraction(1), max(Fraction(0), x))`. The four terminal dimensions
are exact rational values multiplied by 100:

```text
obligation_coverage =
    100, if required_payments_due == 0
    100 * clamp01(required_payments_met / required_payments_due), otherwise

liquidity_retention =
    100 * clamp01(unencumbered_liquidity / initial_liquidity)

cost_efficiency =
    100 * clamp01(
        1 - (borrowing_cost + avoidable_cost) / cost_budget
    )

plan_feasibility =
    100, if remaining_plan_need == 0
    100 * clamp01(
        (unencumbered_liquidity + confirmed_inflows) / remaining_plan_need
    ) / (1 + late_payments), otherwise
```

All four dimensions are in the closed interval 0-100. A terminal
`branching_scenario_score` is the exact rational weighted sum in the formula
above; it is not rounded before the six-scenario judgment mean.

The required-payment invariant is evaluated on linked terminal states. If an
otherwise identical action pays an additional amount `delta > 0`, then
`required_payments_met` increases by `delta`, liquid resources decrease by at
most `delta`, costs/essentials/inflows/unfunded commitments do not worsen, and
`late_payments` does not increase. Under those constraints, unencumbered
liquidity cannot decrease, remaining plan need decreases, obligation coverage
strictly increases until full coverage, and every other dimension is
non-decreasing. Therefore missing that payment cannot improve the scenario
score. State-transition definitions must reject any transition that violates
the state domains or this conservation rule. The zero-denominator rules,
clamping, exact arithmetic, comparison rule, and serialization order are fixed
before the branching engine is implemented.

### Unscored behavior profile

Use `Never / Rarely / Sometimes / Often / Always / Not applicable` for:

- recording expected inflows, outflows, and due dates;
- checking available cash before non-essential spending;
- reserving required payments before discretionary spending;
- comparing total repayment, including fees, before borrowing;
- contacting a counterparty early when a shortfall is expected;
- reviewing expected inflows and outflows at least weekly.

This profile is diagnostic only because anonymous self-report can be faked.

### Optional narrative

The optional prompt may ask the user to describe a financial or business
challenge. It must not be scored, classified, required, retained, or logged.

## Anonymous integrity boundary

The system should resist bundle inspection, invented IDs, form swapping,
replay, direct perfect-payload submission, fixed-form memorization, and edited
result displays. It cannot prove respondent identity or prevent calculators,
search, another person answering, screenshots, multiple devices, or distributed
black-box probing. The score therefore measures demonstrated knowledge and
judgment, not real behavior.

Each attempt receives new numeric values, scenario variants, opaque presentation
IDs, randomized option order, and a single-use signed token. The token is sent
only in an HTTPS `Authorization` header during scoring; it is never placed in a
URL, referrer, browser persistent storage, or any log. Verification URLs carry
only the opaque non-secret `result_id`, and responses set `Cache-Control:
no-store` and `Referrer-Policy: no-referrer`. Immediate retakes are allowed
without cooldown, but each retake receives a new form.

## Phase 0 - Baseline and specification freeze

### Luna work

- Preserve all current branch changes and record the exact HEAD and dirty state.
- Run and record current frontend lint/build and backend test status.
- Freeze contract `2.0`, assessment `india-en-3.0.0`, and scoring policy
  `readiness-rubric-1.0.0`.
- Document every public field, formula, claim boundary, and threat boundary.
- Inventory v1 runtime, model, analytics, artifact, and documentation paths that
  will later be retired or archived.
- Do not change scoring behavior.

### Review gate

- No existing work is lost.
- The specification has no formula or naming conflict.
- Baseline failures are documented rather than silently fixed.
- No later-phase implementation is mixed in.

## Phase 1 - Canonical instrument and objective scorer

### Luna work

- Build one backend-owned instrument specification.
- Separate public-safe prompts from server-only keys, rubric values, generation
  rules, rationales, and bounds.
- Implement the eight seeded objective generators.
- Implement four static SJT definitions and server-only 0-to-3 rubrics.
- Define the behavior profile and optional narrative as unscored.
- Do not add API endpoints or branching logic yet.

### Required tests

- Thousands of seeded forms with independent arithmetic recomputation.
- Exact boundaries and no legacy tolerance credit.
- Same seed produces the same form; distinct seeds vary appropriately.
- No ties, ambiguous keys, invalid values, or out-of-range answers.
- Static SJT normalization is exact.
- Sanitized serialization contains no keys, weights, or rubric points.
- Unknown canonical item and option IDs are rejected.

### Review gate

- Backend is the single instrument authority.
- Generated questions are mathematically valid.
- No public serialization leaks scoring authority.
- No scorer dependency on XGBoost features or artifacts.

## Phase 2 - Branching financial-state engine

### Luna work

- Implement both three-stage simulations as pure state transitions.
- Keep all outcomes deterministic.
- Derive the terminal score from obligation coverage, liquidity, avoidable cost,
  and plan feasibility.
- Produce structured state-transition evidence for later explanations.
- Do not add network or frontend integration.

### Required tests

- Exhaustively execute all 54 complete paths.
- Verify every terminal state and score.
- Property-test monotonicity and dominance invariants.
- Verify all scores remain within 0-to-100.
- Verify identical states score identically.
- Verify no hidden stage bonus or double counting.

### Review gate

- No branch has a manually authored final total.
- Every route is reachable, deterministic, and tested.
- Financially worse terminal states cannot accidentally score higher.
- Branch depth does not change total influence.

## Phase 3 - Unified deterministic scorer

### Luna work

- Combine the eight objective items, four static SJTs, and two branching
  simulations into one pure scoring service.
- Return both domain scores, final index, legacy transformation, unscored
  profile, limitations, and the complete unsigned `Explanation` object frozen
  above. Phase 3 owns objective worked calculations, static-SJT principle text,
  branching state replay, formula reconciliation, and deterministic
  recommendation evidence; it does not sign or expose an API response.
- Build it beside v1 without public cutover.

### Required tests

- Lowest, perfect, mixed, and domain-imbalanced profiles.
- All 101 possible canonical values map correctly to the legacy scale.
- Missing scored answers fail instead of receiving neutral values.
- Behavior, narrative, telemetry, timing, device, ordering, and revision data
  cannot change scores.
- Explanatory contributions reconcile exactly with final output.
- Every generated objective type has a correct worked solution, every branching
  path replays to its terminal state, and recommendation evidence references an
  actual weakness or the maintenance case.

### Review gate

- One pure function reproduces every returned score.
- No model artifact or hidden post-processing adjustment is used.
- All six judgment scenarios receive equal weight.

## Phase 4 - Secure anonymous API

### Luna work

Add:

- `GET /api/v2/assessment/form`
- `POST /api/v2/assessment/score`
- `GET /api/v2/results/verify/{result_id}`
- `GET /api/live`
- `GET /api/ready`

On issuance, generate an attempt ID, nonce, parameterized form, SJT variants,
branching content, opaque presentation IDs, and randomized option order. Store
the canonical mapping in an in-memory cache with
`ATTEMPT_TTL_SECONDS=2700` and `ATTEMPT_STORE_MAX_ENTRIES=10000`, and return a
signed attempt token. Attempt-store expiry, lookup, insertion, and atomic
consumption are serialized under one store lock. Expired entries return
`attempt_expired`; a capacity-evicted or restart-lost entry returns
`attempt_stale`. Before insertion, remove expired records and, if still at
capacity, evict the record with the earliest `(expires_at, issued_at,
attempt_id)` tuple.

The first valid submission consumes the attempt atomically. Immediate retry is
allowed with a new form. Return structured errors for expired, consumed,
unavailable, stale, malformed, unknown-option, rate-limited, and not-ready
states.

Sign every result with result ID, attempt ID, scores, versions, release SHA,
issue/expiry time, `integrity_status="verified_attempt"`, and an
`explanation_digest` using the frozen canonicalization and encodings. Phase 4
serializes the Phase 3 `Explanation`, computes its digest, builds the signing
projection, and stores only the exact redacted `VerificationResponse` in the
24-hour/10,000-entry verification store. The verification endpoint returns
that signed redacted record and must not expose raw answers, behavior values,
narrative, option-selection timelines, or the hidden rubric. The detailed
explanation returned on the initial score response is bound by the digest but
is intentionally not returned by verification. Expired, evicted, and
restart-lost result records return 404 `result_not_found`; signature or digest
failures return `integrity_failed` and never return an unsigned summary.

Use `Cache-Control: no-store`. Do not log raw answers, narrative, tokens, or raw
IP addresses. Apply form and scoring limits of burst 10/minute and sustained
30/hour using short-lived salted network hashes.

### Required tests

- Attempt-token tampering plus result-record, result-signature, and
  explanation-digest tampering; no result token exists or may be introduced.
- Atomic replay and concurrent duplicate submission.
- Cross-attempt answer reuse and invented options.
- Expired, consumed, stale, and lost-cache attempts.
- Immediate retry produces a different form.
- Missing signing secret makes readiness return 503.
- Verification exposes no raw responses.
- Verification-store TTL, capacity eviction, process-loss behavior, signature
  projection, and explanation-digest canonicalization.
- Abuse limits do not create a normal retry cooldown.

### Review gate

- Technical payload and result manipulation is blocked.
- Failures are explicit and recoverable.
- Production cannot become ready without required integrity configuration.

## Phase 5 - Frontend assessment migration

### Luna work

- Fetch the v2 form instead of importing a local scoring bank.
- Render opaque numeric, static SJT, branching, diagnostic, and narrative items.
- Preserve server IDs and randomized order.
- Prevent accidental duplicate submission and fix StrictMode cancellation.
- Recover from expired/consumed attempts with a new form.
- Provide immediate retry without cooldown.
- Store only the signed result in `sessionStorage`, with a 24-hour UI expiry and
  clear action.
- Handle 409, 422, 429, timeout, cancellation, and 503 without page reload.
- Preserve full keyboard, screen-reader, focus, mobile, and reduced-motion
  behavior.

### Required tests

- Form load, version mismatch, numeric validation, and branching navigation.
- StrictMode submission and duplicate prevention.
- Retry obtains a fresh attempt.
- Expired/consumed recovery and stale cache invalidation.
- Production bundle scan rejects answer keys, rubric values, feature signals,
  weights, generation tables, and secrets.
- Frontend lint and production build.

### Review gate

- Frontend contains no scoring authority.
- No submission can remain stuck.
- Every retry gets a new server form.
- Assessment remains accessible and responsive.

## Phase 6 - Result explainability

### Luna work

Phase 6 implements the result presentation only after the scorer and API
stabilize. It consumes the frozen `Explanation` created in Phase 3 and returned
by Phase 4; it must not invent new backend explanation fields, scoring math,
signing projections, or recommendation evidence.

The result experience must show:

1. Primary 0-to-100 index, secondary illustrative 300-to-850 value, domain
   scores, integrity status, and limitations.
2. Exact formula reconciliation: objective contribution, judgment contribution,
   final index, and legacy transformation.
3. For each consumed objective item: issued values, submitted answer, correct
   answer, worked calculation, and concept explanation.
4. For each branching simulation: starting state, decision timeline, state
   changes, terminal state, and the four outcome dimensions.
5. For static SJTs: the financial principle, what the chosen action protects or
   risks, and a stronger principle without exposing the complete hidden rubric.
6. Deterministic recommendations linked to actual missed concepts or weak
   terminal dimensions.
7. A verification link for the signed result.

The initial score response is the full explainability payload. The frontend
stores that response in `sessionStorage` for at most 24 hours so the result
experience can show consumed answers and branching evidence after navigation;
the verification link is a separately redacted public proof. If that browser
session is lost, the UI must show the verified summary and limitations rather
than pretending that raw evidence was recovered.

Use a contribution waterfall, domain cards, branching timelines, and worked
solution panels. Do not use SHAP-style language or fabricated guaranteed score
gains.

### Required tests

- Every explanation number reconciles with the scorer.
- Every generated objective type has a correct worked solution.
- Every branching path produces a valid timeline.
- Result pages do not expose unserved forms or full SJT scoring tables.
- Recommendations match actual weaknesses.
- Perfect profiles receive maintenance guidance rather than invented problems.
- Accessibility and responsive rendering pass.

### Review gate

- Explanations are exact, understandable, and non-misleading.
- No explanation weakens anti-gaming controls.
- No ML or personality claims remain in the public result.

## Phase 7 - Legacy separation and runtime cleanup

### Luna work

- After v2 frontend verification, make the active legacy `POST /api/score`
  return `410 Gone`. If a compatibility alias named `/api/v1/score` is ever
  introduced before retirement, it must also return `410 Gone`; the current
  runtime has no `/api/v1/score` route.
- Remove the old scorer from the production dependency graph.
- Archive synthetic XGBoost as `research/legacy_synthetic_model`.
- Exclude model artifacts, SHAP/DiCE, NLP, training scripts, and heavy research
  dependencies from the production image.
- Replace Admin with an optional static Research Lab.
- Disable operational analytics endpoints in production.
- Remove unreachable governance, obsolete parser/question, and confirmed dead
  code.
- Update architecture, API, data, deployment, rollback, and methodology docs.

The Research Lab must state that labels and fairness reports are synthetic,
AUC measures recovery of generated data, and the model does not score public
assessments.

### Required tests

- Production imports no archived research modules.
- v1 cannot score.
- Public readiness does not depend on ML artifacts.
- Research routes cannot affect public results.
- Production runtime contains only serving dependencies.
- Stale-term and stale-version documentation scans pass.

### Review gate

- Research and public scoring are genuinely isolated.
- No referenced runtime file is deleted accidentally.
- Production image and dependency surface are materially smaller.

## Phase 8 - CI, deployment, and operational hardening

### Luna work

- Make frontend lint/build and all backend suites blocking.
- Add generator fuzz, branch exhaustiveness, contract, anti-cheat, and bundle
  secrecy checks.
- Replace obsolete reproducibility scripts and absolute stability claims.
- Gate deployment on successful CI for one exact Git SHA.
- Require matching frontend/backend release metadata and signing configuration.
- Use readiness for Docker and uptime monitoring.
- Fail when deployment credentials are absent rather than silently skipping.
- Add post-deploy contract, version, form, score, and result-verification smoke
  checks.
- Add whole-release rollback for the matching frontend/backend pair.

Deployment is performed only when separately authorized.

### Review gate

- A bad commit cannot deploy.
- An unhealthy scorer cannot appear ready.
- Frontend/backend version mismatch is detectable and recoverable.
- Rollback restores a coherent release pair.

## Phase 9 - Final audit and handoff

### Luna work

Produce a final report with architecture, resolved loopholes, question inventory,
formula, threat model, remaining limitations, tests, dependency/artifact
inventory, API migration, deployment/rollback steps, and future validation
roadmap.

### Codex final review

Codex performs a whole-repository review, full tests/build, arithmetic and branch
verification, explanation reconciliation, adversarial API testing, bundle
inspection, privacy/logging audit, fail-closed inspection, and manual browser
testing when the tooling is available.

Codex fixes all in-scope final-audit defects and repeats verification. Final
status is either `READY FOR PORTFOLIO DEPLOYMENT` or `BLOCKED` on missing
authority/external state. The project is complete only after every phase passes.

## Future-only roadmap

- expert review and cognitive interviews;
- India-English pilot and equivalent-form calibration;
- reliability, item discrimination, and differential-item-functioning work;
- representative reference distributions;
- consented longitudinal outcomes and external validation;
- account-based attempt history if the system ever becomes high-stakes;
- Redis-backed attempt storage if the service scales beyond one replica.
