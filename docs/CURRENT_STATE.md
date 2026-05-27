# Current State

**Date:** May 27, 2026  
**Phase:** Monotonic XGBoost promoted, Q&A session lockout resolved, validity suite fully green  
**Active Runtime:** Manifest-backed `xgboost_monotonic` (classical_monotonic type)  
**Manifest:** `models/registry/production_manifest.json`  
**Manifest Version:** `xgboost_monotonic_v2`  
**Branch:** `main` (Locked in manifest `code_ref` as `antigravity/dev`)

## Status Summary

The backend is fully stabilized, manifest-backed, and verified with the latest monotonic XGBoost model. Default startup loads `models/registry/production_manifest.json`, validates checksums, and serves the checked-in `xgboost_monotonic` runtime bundle (including preprocessor, text PCA projection, SHAP explainer, DiCE explainer, and analytics reports).

The borrower frontend contains a complete, optimized React client which successfully compiles via Vite into production assets. Standard Node.js-based unit testing scripts are active and 100% green. We successfully resolved the persistent Q&A attempt lockout by introducing a custom session-reset "Run again" handler and an on-card "Start over" state controller.

The evaluator dashboard is fully complete with `/api/confusion-matrix` rendering a premium 2x2 decision grid. All cards and charts on the dashboard now have modular async spinners, error-handling wrapper boundaries, and empty-state checkers.

A production-style manual deployment runbook (`docs/DEPLOYMENT_RUNBOOK.md`) and a PowerShell orchestrator (`scripts/setup/start_alterscore.ps1`) are available to manage and launch services.

## Checked-In Runtime Snapshot

- Runtime model: `xgboost_monotonic`
- Runtime type: `classical_monotonic`
- Test AUC: `0.7547` (governed with strict monotonicity constraints on key behavioral features)
- Fairness status: Overall AUC `0.7547`, with designated verdict: "Model shows acceptable fairness across all tested demographic groups. No subgroup shows AUC deviation >4% from the overall model."
- Validity check status: 100% PASS on the python-based score-inflation validity audit.

## What Is Stable & Verified

- Monotonic XGBoost candidate promoted to production (v2 assessment) with SHA256 checksum validations.
- Automated local startup and orchestrator scripts (`start_alterscore.ps1`).
- Borrower Q&A persistent lockout resolved; session-reset handlers for "Run again" and "Start over" fully active and operational.
- Frontend test runner script (`npm run test`) with zero failures.
- Production UI builds with optimized asset routing.
- Dashboard confusion matrix, localized loaders, and card-level error states fully implemented and verified.

## What Remains Open (Next Recommended Steps)

* **Dashboard/Chart Layout:** Minor mobile overflow handling for charts and tables on extremely narrow viewports (e.g. mobile devices below 360px width).
* **Rollback Checklist:** Rollback checklist tied to manifest versions for quick-response recovery scenarios.


