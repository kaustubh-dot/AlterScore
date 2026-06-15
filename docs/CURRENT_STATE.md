# Current State

**Date:** June 15, 2026
**Phase:** Calibrated monotonic XGBoost serving as promoted checked-in runtime; blocking promotion gates pass
**Active Runtime:** Manifest-backed `xgboost_monotonic` (classical_monotonic type)
**Manifest:** `models/registry/production_manifest.json`
**Manifest Version:** `xgboost_monotonic_calibrated_v4`
**Promotion Gate Policy:** `models/registry/promotion_gate_policy.json` (`promotion_gate_policy_v2`)
**Branch:** `main`

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
- Score mapping: manifest-declared FICO-style `log_odds` mapping (`score_base=595`, `log_odds_factor=64.92`, `probability_clip_min=0.000001`, `probability_clip_max=0.99`, `calibration=isotonic`). Base and factor are derived from interpretable policy knobs (PDO=45, anchor 640 @ 2:1 odds) in `backend/app/core/constants.py` — never hand-edited.
- Score driver: creditworthiness rests on hard-to-fake evidence — objective cognition (`numeracy_score` is the #1 SHAP feature, with CRT and financial literacy in the top 3) and scenario psychometrics. Spoofable process-timing telemetry (`scroll_hesitation_score`, `session_duration_sec`) is excluded from the causal label and feeds only the anti-gaming governance multiplier.
- Test AUC: `0.7787` (checked-in monotonic runtime evaluated on held-out months `11-12`)
- Expected calibration error: `0.0346` (passes the current promotion gate)
- Fairness status: Overall AUC `0.7787`; no subgroup shows AUC deviation >4% from the overall model.
- Individual-fairness proxy: flagged-pair share `0.027`, max similar-pair score gap `130`; both pass the current promotion gate. Similarity is measured over the model's active (non-masked) features only.
- Anti-gaming: governance gaming-stack escalation drops mechanical/gaming profiles (2+ stacked signals — straight-lining, fast-pattern scenario gaming, near-zero engagement) to the score floor regardless of answer correctness.
- Drift status: PSI verdict `stable`, max PSI `0.0152` (all features stable across months).
- Validity check status: 100% PASS on the python-based score-inflation validity audit.

## What Is Stable & Verified

- Calibrated monotonic XGBoost runtime is checksum-validated and marked `promoted`; all blocking gates pass under `promotion_gate_policy_v2`.
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
