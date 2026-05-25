# Current State

**Date:** May 25, 2026  
**Phase:** Pre-pilot hardening complete, local manual release validation ready  
**Active Runtime:** Manifest-backed monotonic `XGBoost`  
**Manifest:** `models/registry/production_manifest.json`  
**Manifest Version:** `xgboost_monotonic_v1`  
**Branch:** `main` (Locked in manifest `code_ref`)

## Status Summary

The backend is fully stabilized, manifest-backed, and verified. Default startup loads `models/registry/production_manifest.json`, validates checksums, and serves the checked-in `xgboost_monotonic` runtime bundle. The manifest `code_ref` has been formally updated to the stable `"main"` branch.

The borrower frontend contains a complete, optimized React client which successfully compiles via Vite into production assets. Standard Node.js-based unit testing scripts are now active and passing (all 9 core data and payload assertions pass).

The evaluator dashboard is fully complete with `/api/confusion-matrix` rendering a premium 2x2 decision grid. All cards and charts on the dashboard now have modular async spinners, error-handling wrapper boundaries, and empty-state checkers.

A production-style manual deployment runbook (`docs/DEPLOYMENT_RUNBOOK.md`) and a PowerShell orchestrator (`scripts/setup/start_alterscore.ps1`) are available to manage and launch services.

## Checked-In Runtime Snapshot

- Runtime model: `xgboost_monotonic`
- Runtime type: `classical_monotonic`
- Test AUC: `0.8040` (reconciled raw baseline)
- Brier score: `0.1514`
- ECE: `0.0284`
- PSI verdict: `stable`
- Fairness status: Formally accepted subgroup variance for `gender=non_binary` based on sample count support limits (57 samples) and non-discrimination AUC performance (`0.7468`).

## What Is Stable & Verified

- Manifest-backed backend startup with SHA256 checksum validations.
- Automated local startup and orchestrator scripts (`start_alterscore.ps1`).
- Borrower assessment telemetry and score payload conversions.
- Frontend test runner script (`npm run test`) with zero failures.
- Production UI builds with optimized asset routing.
- Dashboard confusion matrix, localized loaders, and card-level error states.

## What Remains Open (Next Recommended Steps)

* **E.1/E.2 Visual QA:** Run browser visual screenshot checks for borrower flows on mobile viewports (e.g. 375px) to ensure gsap/WebGL layouts fit perfectly.
* **E.7 Bundle Optimization:** Set up Rollup chunking rules in `vite.config.js` to split the React Three Fiber (R3F) bundle chunks if web load-times require it.
* **F.4 Dashboard Tests:** Mock client-side payloads in the frontend to cover edge-case dashboard data failures.
* **G.3 Release Smoke Checks:** Finalize demo walkthrough scripts and manual release checklists for the pilot team.
