# AlterScore Roadmap

## Roadmap Principles

- Contracts before implementation.
- Offline artifacts before online serving changes.
- Temporal-split validation before promotion claims.
- Backend contract stability before frontend feature coupling.
- Report-backed analytics before dashboard visuals.
- Manifest-backed reproducibility before release/demo packaging.
- Fairness and calibration claims must match the checked-in serving bundle.

## Current Status Summary

| Track | Status | Notes |
|---|---|---|
| Track A - Governance | Complete, monitoring open | Fairness, calibration parity, individual-fairness proxy exist; current promoted report still needs `gender=non_binary` review |
| Track B - Neural Training | Complete | TabNet + MLP remain benchmark/research artifacts |
| Track C - Ensemble & Calibration | Complete, no longer active runtime | Calibrated stacking ensemble remains a benchmark and rollback/reference bundle |
| Track D - Explainability & Promotion | Complete | SHAP, DICE, global importance, manifest validation |
| Track D+ - Ensemble Serving Runtime | Complete, reference path | Adapter and tests remain useful for rollback/benchmarking |
| Track D++ - Governed Constrained Trees | Promoted | `xgboost_monotonic` is the checked-in manifest runtime |
| Track E - Borrower Frontend | Implemented, QA pending | Assessment, submission, processing, results, sharing/export |
| Track F - Evaluator Dashboard | Partial | Most analytics endpoints consumed; confusion matrix, panel states, and tests remain |
| Track G - Release & Demo | Pending | Local/manual runbook, release checklist, and demo script remain |

## Program Tracks

### Track A - Governance Completion

Core governance reports exist. The current priority is not adding another
metric, but reconciling the promoted monotonic runtime bundle with the
governed full-run review:

- checked-in runtime report: AUC `0.8040`, Brier `0.1514`, ECE `0.0284`
- governed full-run review: AUC `0.8090`, Brier `0.1496`, ECE `0.0207`
- checked-in fairness verdict: attention required for `gender=non_binary`

### Track B - Neural Offline Training

Closed. TabNet and MLP training modules, CLI entrypoints, artifacts, and smoke
tests are present. TabNet remains research-only unless a future candidate
passes the same monotonic and counterfactual gates.

### Track C - Ensemble And Calibration

Closed as an implementation track. The calibrated stacking ensemble remains a
validated benchmark and rollback/reference path, but the active manifest now
serves monotonic `XGBoost`.

### Track D - Production Explainability Refresh

Closed. SHAP, DICE, global importance, fairness, PSI, and percentile artifacts
are present for the checked-in runtime bundle.

### Track D+ - Ensemble Serving Runtime

Closed as a reference runtime path. The backend still supports ensemble
bundles when the manifest declares `runtime_model_type: "ensemble"`, but the
current default manifest is `classical_monotonic`.

### Track D++ - Governed Constrained Trees

Promoted. Monotonic `XGBoost` is now the checked-in runtime. The remaining
work is hardening and documentation around the promoted bundle, especially the
fairness attention item and metric/report reconciliation.

### Track E - Borrower Frontend

Implementation is present. Remaining work is QA and test coverage:

- Browser screenshot QA for landing, assessment, processing, and results.
- Mobile checks at 375px and common desktop widths.
- Focused tests for question data, telemetry, score payloads, retry behavior,
  missing results state, and rendering of SHAP/action/eligibility blocks.
- Optional bundle optimization for the R3F vendor chunk if demo performance
  requires it.

### Track F - Evaluator Dashboard

Partial. The dashboard currently consumes health, model stats, baseline,
fairness, drift, global importance, score distribution, ROC, PR, and
calibration endpoints. Remaining work:

- Render `/api/confusion-matrix`.
- Add independent loading, error, empty, and success states per panel.
- Add dashboard tests with mocked endpoint payloads and failure cases.
- Improve mobile overflow handling for charts and tables.
- Decide whether to expose runtime model name/type directly from `/api/health`
  instead of deriving it from the manifest id in the frontend.

### Track G - Release And Demo

Image-based packaging is intentionally out of scope. Required before
treating release/demo readiness as complete:

- Write a local/manual runbook for starting backend and frontend.
- Define production-style environment variables for a manual host.
- Validate backend startup and frontend build from a clean local setup.
- Finalize release smoke-test checklist.
- Write demo walkthrough script and rollback notes tied to manifest versions.

## Recommended Execution Order

```text
D++.1 runtime report/fairness reconciliation
  -> E.4 borrower QA/tests
  -> F.1 dashboard confusion matrix and panel states
  -> F.2 dashboard responsive polish
  -> G.1 local/manual release runbook
  -> G.2 release checklist
  -> G.3 demo script
```

## Known Technical Debt

- Promoted monotonic runtime report metrics do not exactly match the governed
  full-run review metrics.
- Checked-in fairness report requires attention for `gender=non_binary`.
- `production_manifest.json` still records historical `code_ref:
  "antigravity/dev"` instead of a release branch/commit identifier.
- Dashboard still derives active model identity from `manifest_version`.
- Frontend unit/E2E coverage is thin for borrower flow and dashboard failures.
- Release/demo runbook is still pending.

## PRD Mapping

| PRD Section | Track |
|---|---|
| Sections 8, 13.1 | Track A governance - implemented, fairness hardening open |
| Section 7 | Tracks B, C, D ML pipeline - implemented; active runtime superseded by governed monotonic XGBoost |
| Section 9 | Track D+/D++ serving runtime - implemented |
| Section 10 | Track E borrower frontend implemented; Track F dashboard partial |
| Section 12 | Track G release/demo readiness - pending |
