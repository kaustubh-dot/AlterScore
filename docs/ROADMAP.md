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
| Track A - Governance | Complete, monitoring open | Fairness, calibration parity, individual-fairness proxy exist; current promoted report contains age and education group metrics |
| Track B - Neural Training | Complete | TabNet + MLP remain benchmark/research artifacts |
| Track C - Ensemble & Calibration | Promoted | Calibrated stacking ensemble is the active manifest runtime (`calibrated_stacking_ensemble_v1`) |
| Track D - Explainability & Promotion | Complete | SHAP, DICE, global importance, manifest validation |
| Track D+ - Ensemble Serving Runtime | Promoted | Stacking ensemble fully integrated and served via manifest-backed routing |
| Track D++ - Governed Constrained Trees | Complete, rollback path | Monotonic `xgboost` remains a validated alternative and rollback runtime |
| Track E - Borrower Frontend | Complete | Q&A session lockout resolved; session reset handlers for "Run again" and "Start over" fully active |
| Track F - Evaluator Dashboard | Partial | Most analytics endpoints consumed; confusion matrix, panel states, and tests remain |
| Track G - Release & Demo | Pending | Local/manual runbook, release checklist, and demo script remain |

## Program Tracks

### Track A - Governance Completion

Core governance reports exist. The current priority is not adding another
metric, but maintaining the promoted stacking ensemble runtime bundle:

- Promoted runtime: `stacking_ensemble`
- Test AUC: `0.7945`
- Calibration method: `isotonic`
- Score midpoint: calibrated to `500`

### Track B - Neural Offline Training

Closed. TabNet and MLP training modules, CLI entrypoints, artifacts, and smoke
tests are present. TabNet and MLP base models are actively served within the promoted stacking ensemble!

### Track C - Ensemble And Calibration

Promoted. The calibrated stacking ensemble has been re-trained on CUDA maximum performance mode and promoted to the active `production_manifest.json` as version `calibrated_stacking_ensemble_v1`.

### Track D - Production Explainability Refresh

Closed. SHAP, DICE, global importance, fairness, PSI, and percentile artifacts
are present for the checked-in stacking ensemble runtime bundle.

### Track D+ - Ensemble Serving Runtime

Promoted. Stacking ensemble is the active serving runtime, supported natively by FastAPI's endpoint scoring.

### Track D++ - Governed Constrained Trees

Closed as a rollback path. Monotonic `XGBoost` remains a validated benchmark and alternative runtime.

### Track E - Borrower Frontend

Complete. The borrower flow has been fully completed and hardened:
- Resolved browser/refresh session lockout by redirecting completed sessions to `/results`.
- Added custom session-reset "Run again" handler to completely clear cached states.
- Implemented mid-assessment "Start over" controls to let users reset progress.
- Node unit tests cover all questions and score payloads.
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
