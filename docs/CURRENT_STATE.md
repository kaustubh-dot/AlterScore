# Current State

**Date:** June 11, 2026
**Phase:** Calibrated monotonic XGBoost serving as promoted checked-in runtime; blocking promotion gates pass
**Active Runtime:** Manifest-backed `xgboost_monotonic` (classical_monotonic type)
**Manifest:** `models/registry/production_manifest.json`
**Manifest Version:** `xgboost_monotonic_calibrated_v1`
**Promotion Gate Policy:** `models/registry/promotion_gate_policy.json` (`promotion_gate_policy_v1`)
**Branch:** `main` (merged from `codex-scoring-calibration-roadmap` on 2026-06-11)

## Status Summary

The backend is manifest-backed and serves the checked-in calibrated monotonic XGBoost runtime bundle. Default startup loads `models/registry/production_manifest.json`, validates checksums, and serves the checked-in `xgboost_monotonic` bundle (including preprocessor, text PCA projection, SHAP explainer, DiCE explainer, and analytics reports). Blocking promotion gates now pass; health still surfaces the non-blocking PSI watch on `avg_response_time_ms`.

The borrower frontend contains a complete, optimized React client which successfully compiles via Vite into production assets. Standard Node.js-based unit testing scripts are active and 100% green. We successfully resolved the persistent Q&A attempt lockout by introducing a custom session-reset "Run again" handler and an on-card "Start over" state controller.

The evaluator dashboard is fully complete with `/api/confusion-matrix` rendering a premium 2x2 decision grid. All cards and charts on the dashboard now have modular async spinners, error-handling wrapper boundaries, and empty-state checkers.

The borrower visual layer has been rebuilt as a cinematic, route-aware WebGL
experience. A persistent Credit Signal Core now carries the user from a
quieter assessment halo into a focused processing state and the score reveal.
The landing route now renders a separate original Signal Corridor inside that
same canvas: a long forward fly-through with tunnel frames, rails, glyph
planes, signal nodes, fog, and sparse HUD overlays. Static landing background
cross-fades and the dormant orb prototype were removed. Adaptive quality tiers
preserve the same visual story on desktop, tablet, and mobile while reducing
WebGL cost.

A production-style manual deployment runbook (`docs/DEPLOYMENT_RUNBOOK.md`) and a PowerShell orchestrator (`scripts/setup/start_alterscore.ps1`) are available to manage and launch services.

## Checked-In Runtime Snapshot

- Runtime model: `xgboost_monotonic`
- Runtime type: `classical_monotonic`
- Score mapping: manifest-declared `log_odds` mapping (`score_base=575`, `log_odds_factor=28`, `probability_clip_min=0.000001`, `probability_clip_max=0.99`, `calibration=isotonic`)
- Test AUC: `0.7521` (checked-in monotonic runtime re-evaluated on held-out months `11-12`)
- Expected calibration error: `0.0316` (passes the current promotion gate)
- Post-governance AUC: `0.7514`
- Fairness status: Overall AUC `0.7521`, with designated verdict: "Model shows acceptable fairness across all tested demographic groups. No subgroup shows AUC deviation >4% from the overall model."
- Individual-fairness proxy: flagged-pair share `0.0069`, max similar-pair score gap `70`; both pass the current promotion gate.
- Drift status: PSI verdict `stable`, max PSI `0.0147` (all features stable across months, temporal drift resolved).
- Validity check status: 100% PASS on the python-based score-inflation validity audit.

## What Is Stable & Verified

- Calibrated monotonic XGBoost runtime is checksum-validated and marked `promoted`; all blocking gates pass under `promotion_gate_policy_v1`.
- Automated local startup and orchestrator scripts (`start_alterscore.ps1`).
- Borrower Q&A persistent lockout resolved; session-reset handlers for "Run again" and "Start over" fully active and operational.
- Frontend test runner script (`npm run test`) with zero failures.
- Production UI builds with optimized asset routing.
- Dashboard confusion matrix, localized loaders, and card-level error states fully implemented and verified.
- Original responsive signal-landscape WebP assets and persistent borrower
  WebGL canvas implemented with mobile fidelity reduction and reduced-motion
  behavior.
- Landing route upgraded to an original Sidewave-inspired behavioral twin:
  fixed HUD, approximately 89-viewport desktop scroll corridor, spatial text
  staging, one fixed WebGL canvas, and final assessment CTA handoff.
- Rollback checklist tied to manifest versions ([ROLLBACK_CHECKLIST.md](file:///C:/Kaustubh/Projects/AlterScore/docs/ROLLBACK_CHECKLIST.md)) fully documented.
- Minor mobile overflow handling for charts and tables on extremely narrow viewports (<360px) fully implemented.
- De-trended synthetic generator and retrained model bundle, resolving response-time PSI watch (max PSI is now `0.0147`, verdict: stable).
- Promotion gate checking (`promotion_gates.py`) wired directly into the CI validation pipeline.

## What Remains Open (Next Recommended Steps)

* **Borrower E2E Recheck:** Run one real `/api/score` browser walkthrough on a
  machine with the backend environment installed; the current UI workstation
  does not have `uvicorn` available.
