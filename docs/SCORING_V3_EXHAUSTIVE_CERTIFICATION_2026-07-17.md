# Scoring v3 exhaustive certification — 2026-07-17

## Decision

The branch is an unconditional local release candidate. The previously open
scale-calibration defect was resolved after explicit policy approval by
implementing exact feasible-range normalization under
`readiness-rubric-1.1.0`. The strongest feasible response profile now produces
knowledge 100.00, judgment 100.00, both branching scores 100.00, and a signed
Financial Decision Index of 100.

No deployment, rollback, or external production mutation was performed during
this certification.

## Scope

The audit covered the active backend, public v2 API, canonical form generator,
all 54 branching paths, unified score composition, signing and replay controls,
frontend form/result/dashboard/research routes, responsive and failure states,
release automation, rollback provenance, dependencies, and active-source
encoding.

Three independent lightweight reviewers examined:

- scoring, API security, deterministic arithmetic, and anti-gaming controls;
- frontend contract validation, accessibility, responsive rendering, and
  session privacy;
- release/rollback trust, dependency locks, action pins, and legacy isolation.

The primary audit independently reproduced and browser-tested the important
findings before accepting or changing code.

## Automated certification

| Gate | Result |
|---|---|
| Complete backend suite | PASS — 257 tests |
| Generated-form/property sweep | PASS — 1,000 generated forms |
| Branching exhaustiveness | PASS — all 54 complete paths per sweep; deterministic, bounded, replayable |
| Frontend contract tests | PASS — 11 tests |
| Frontend explainability tests | PASS — 8 tests |
| Frontend separation tests | PASS — 3 tests |
| Frontend release tests | PASS — 4 tests |
| Frontend lint | PASS |
| Production frontend build | PASS — 1,844 modules transformed |
| Production dependency audit | PASS — 0 vulnerabilities |
| Python static analysis | PASS |
| Rollback/release adversarial tests | PASS — included in the 257-test suite |
| Workflow YAML parse | PASS |
| Active-source UTF-8 sentinel scan | PASS — no mojibake sentinel code points |
| Git whitespace check | PASS |

## Local browser certification

The complete frontend and API were hosted locally and exercised through the
browser at desktop, 1024×768, and 390×844 viewports.

Verified journeys and states:

- landing, assessment consent, issued-form load, and a fresh form on retry;
- required numeric validation for blank, decimal, and unsafe-integer input;
- back navigation, retained answers, reset confirmation, exit confirmation,
  and focus transfer to each new question heading;
- all eight objective items, four static judgment items, six branch decisions,
  six unscored behavior reflections, and the optional narrative step;
- the globally strongest feasible response path, signed submission, formula
  reconciliation, worked objective evidence, decision replay, limitations,
  recommendations, and verification response;
- detailed-result refresh persistence while unscored reflection data is
  removed after its one permitted display;
- dashboard summary, verification URL, session clearing, and direct result
  access after clearing;
- research boundary page;
- backend-offline form failure, fail-closed error UI, retry, and recovery;
- responsive landing, assessment, result, dashboard, and not-found layouts.

## Findings and corrections

### P2 — rollback artifact provenance was under-bound — fixed

The old rollback workflow could accept a same-name artifact based mainly on
SHA/branch/event metadata. It did not prove that the artifact came from the
approved successful deployment workflow.

The repaired flow now:

1. requires dispatch from the current `main` control-plane commit;
2. resolves the exact active `deploy-hf.yml` workflow ID through the GitHub API;
3. accepts only a completed successful same-repository `workflow_run` for the
   requested `main` SHA and exact workflow ID/name/path;
4. queries artifacts only inside that selected run and requires exactly one
   non-expired, positive, bounded artifact with matching run/repository IDs;
5. binds the manifest workflow URL to the exact selected run ID;
6. validates a root-only, non-symlink, non-encrypted, size- and
   compression-bounded ZIP and a 40-character backend package commit;
7. retrieves and validates every filtered workflow-run page up to GitHub's
   1,000-result search cap, rejecting missing, duplicate, or unstable pages;
8. runs validation from the current control plane before target checkout.

Adversarial coverage rejects wrong workflow IDs/paths, failed or incomplete
runs, wrong events/branches/SHAs, cross-run artifacts, duplicate artifacts,
wrong manifest run URLs, and unsafe ZIP entries.
Pagination coverage also proves that a trusted run on page two remains
selectable after more than 100 matching executions.

### P3 — unknown routes rendered a blank page — fixed

A wildcard route now renders a semantic, keyboard-accessible recovery page
with Home and Start assessment actions. Desktop and mobile browser checks pass.

### P3 — assessment count wording was ambiguous — fixed

The landing page now distinguishes 24 required items from the optional
reflection. The assessment uses the dynamic wording `Step X of Y`, which also
remains correct if the optional narrative is disabled.

### Encoding concern — disproved; stale workaround removed

Byte-aware UTF-8 inspection and browser rendering confirmed that canonical
currency and arithmetic symbols are valid. A legacy Results-page mojibake
replacement table was unnecessary and has been removed. The active backend and
frontend source graph contains no mojibake sentinel code points.

## Approved scoring-policy migration — resolved

The four terminal dimensions and original weighted composites remain exact and
deterministic. Because each scenario starts with unavoidable constraints, the
raw composite cannot span the advertised 0-to-100 assessment scale. After the
user explicitly approved an assessment-relative interpretation, each scenario
now applies:

```text
normalized = 100 × (raw - feasible_min) / (feasible_max - feasible_min)
```

The engine uses exact `Fraction` arithmetic without pre-quantization, verifies
that the raw score lies inside a positive-width interval, and fails closed
otherwise. Exhaustive tests prove that the stored endpoints equal the actual
minimum and maximum across all 27 paths in each scenario, normalize exactly to
0 and 100, and preserve monotonic ordering across all 54 paths. Recommendation
thresholds operate on the normalized score.

Raw composites and attainable endpoints remain internal diagnostics. Public
results expose `score_basis: feasible_range_normalized`, terminal dimensions,
the calibrated score, and a plain-language same-scenario interpretation. They
do not expose endpoint constants, per-path values, option ranks, or rubric
points. The API rejects `readiness-rubric-1.0.0` without consuming the attempt;
release metadata, manifests, frontend validation, documentation, explanation
digests, and signed projections are aligned on `readiness-rubric-1.1.0`.

The final policy was reproduced through a complete locally hosted public form:

- financial knowledge: 100.00;
- decision judgment: 100.00;
- both calibrated branching scenarios: 100.00;
- signed Financial Decision Index: 100/100;
- illustrative legacy transformation: 850.

## Residual project limitations

- This remains a portfolio demonstration without human or external
  psychometric validation; results are educational readiness evidence, not
  creditworthiness or repayment prediction.
- Attempts and verification records use bounded process memory, so a restart
  can invalidate in-flight attempts or old verification links.
- Live provider deployment and an actual rollback were not executed in this
  local audit.
- Open-source scenario content can always be studied. The implemented controls
  make superficial answer gaming harder through randomized numeric forms,
  plausible options, server-only keys/rubrics, one-time signed attempts, and
  rate limits, but no public self-administered assessment can guarantee that a
  determined user did not learn its content outside the session.
