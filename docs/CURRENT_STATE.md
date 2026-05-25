# Current State

**Date:** May 25, 2026  
**Phase:** Repository audit, runtime alignment, and pre-pilot hardening  
**Active Runtime:** Manifest-backed monotonic `XGBoost`  
**Manifest:** `models/registry/production_manifest.json`  
**Manifest Version:** `xgboost_monotonic_v1`  
**Branch:** `main`

## Status Summary

The backend is implemented and manifest-backed. Default startup from the
repository root loads `models/registry/production_manifest.json`, validates
checksums, and serves the checked-in `xgboost_monotonic` runtime bundle.

The earlier calibrated stacking ensemble remains checked in as a benchmark and
rollback/reference path, but it is no longer the default manifest runtime. The
governed constrained-tree work changed the preferred production path toward a
monotonic tree system because it provides stronger monotonic and
counterfactual behavior with simpler serving requirements.

The borrower frontend is implemented in `frontend/` and includes the landing
page, assessment flow, processing state, results rendering, score sharing, and
API submission to `/api/score`. The evaluator dashboard now consumes most
analytics endpoints, but it still needs confusion-matrix rendering, independent
panel-level loading/error states, and formal browser QA evidence.

## Checked-In Runtime Snapshot

- Runtime model: `xgboost_monotonic`
- Runtime type: `classical_monotonic`
- Test AUC in checked-in report: `0.8040`
- Brier score in checked-in report: `0.1514`
- ECE in checked-in report: `0.0284`
- PSI verdict in checked-in report: `stable`
- Fairness report status: requires attention for `gender=non_binary`

The full governed comparison and fairness-hardening review recorded stronger
candidate metrics (`0.8090` AUC, `0.1496` Brier, `0.0207` ECE), but the
checked-in promoted bundle must be treated as the operational source of truth.
The metric/fairness-report difference is a pre-pilot reconciliation item.

## What Is Stable

- Manifest-backed backend startup
- Checked-in monotonic `XGBoost` runtime artifact bundle under `models/`
- Score, health, and analytics API contracts
- Borrower assessment and results flow
- Backend and pipeline test layout
- Governed monotonic-tree evaluation pipeline

## What Remains Open

- Reconcile the governed full-run metrics with the checked-in promoted
  monotonic runtime reports.
- Resolve or explicitly accept the checked-in fairness attention item for
  `gender=non_binary` before any pilot/demo claim.
- Finish dashboard confusion-matrix rendering and panel-level error states.
- Expand frontend-focused tests and browser QA across target viewports.
- Finalize manual deployment/runbook notes after dashboard work.
- Replace historical `code_ref` values such as `antigravity/dev` with explicit
  branch/commit identifiers during the next formal promotion.

## Immediate Next Steps

1. Run the checked-in runtime smoke suite and frontend build after this audit.
2. Regenerate or document the promoted monotonic runtime reports so metrics,
   fairness verdicts, and manifest notes agree.
3. Finish the remaining dashboard panels and frontend tests.
4. Prepare a local/manual deployment runbook.
5. Prepare a demo/release checklist once Track F validation passes.
