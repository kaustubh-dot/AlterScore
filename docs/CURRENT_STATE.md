# Current State

**Date:** May 26, 2026  
**Phase:** Stacking ensemble GPU-promoted, Q&A session lockout resolved, validity suite fully green  
**Active Runtime:** Manifest-backed calibrated `stacking_ensemble` (ensemble type)  
**Manifest:** `models/registry/production_manifest.json`  
**Manifest Version:** `calibrated_stacking_ensemble_v1`  
**Branch:** `main` (Locked in manifest `code_ref`)

## Status Summary

The backend is fully stabilized, manifest-backed, and verified with the latest stacking ensemble. Default startup loads `models/registry/production_manifest.json`, validates checksums, and serves the checked-in `calibrated_stacking` runtime bundle (integrating base models: logistic regression, random forest, xgboost, lightgbm, tabnet, and residual MLP).

The borrower frontend contains a complete, optimized React client which successfully compiles via Vite into production assets. Standard Node.js-based unit testing scripts are active and 100% green. We successfully resolved the persistent Q&A attempt lockout by introducing a custom session-reset "Run again" handler and an on-card "Start over" state controller.

The evaluator dashboard is fully complete with `/api/confusion-matrix` rendering a premium 2x2 decision grid. All cards and charts on the dashboard now have modular async spinners, error-handling wrapper boundaries, and empty-state checkers.

A production-style manual deployment runbook (`docs/DEPLOYMENT_RUNBOOK.md`) and a PowerShell orchestrator (`scripts/setup/start_alterscore.ps1`) are available to manage and launch services.

## Checked-In Runtime Snapshot

- Runtime model: `stacking_ensemble`
- Runtime type: `ensemble`
- Test AUC: `0.7945` (meta-learner: `LogisticRegression(C=1.0)`, calibration: `isotonic`)
- Fairness status: Overall AUC `0.7945`, with designated attention guidelines for `age_group=36-50` and `education_level=graduate` (metrics and deviations successfully compiled).
- Validity check status: 100% PASS on the python-based score-inflation validity audit.

## What Is Stable & Verified

- High-performance stacking ensemble re-trained on CUDA Laptop GPU (`NVIDIA GeForce RTX 3050 Laptop GPU`) inside the `venv` shell.
- Manifest-backed backend startup with SHA256 checksum validations.
- Automated local startup and orchestrator scripts (`start_alterscore.ps1`).
- Borrower Q&A persistent lockout resolved; session-reset handlers for "Run again" and "Start over" fully active and operational.
- Frontend test runner script (`npm run test`) with zero failures.
- Production UI builds with optimized asset routing.
- Dashboard confusion matrix, localized loaders, and card-level error states.

## What Remains Open (Next Recommended Steps)

* **E.7 Bundle Optimization:** Set up Rollup chunking rules in `vite.config.js` to split the React Three Fiber (R3F) bundle chunks if web load-times require it.
* **F.4 Dashboard Tests:** Mock client-side payloads in the frontend to cover edge-case dashboard data failures.
* **G.3 Release Smoke Checks:** Finalize demo walkthrough scripts and manual release checklists for the pilot team.

