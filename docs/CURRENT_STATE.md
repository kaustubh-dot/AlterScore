# Current State

**Date:** May 24, 2026
**Phase:** Governed production-candidate stabilization
**Active Runtime:** Checked-in calibrated stacking ensemble
**Leading Candidate:** Monotonic `XGBoost` (evaluated, not yet promoted)
**Branch:** `main`

## Status Summary

The backend is implemented and manifest-backed. The default startup path is the
repository-root command `python -m uvicorn backend.app.main:app`, which loads
`models/registry/production_manifest.json`, validates manifest checksums, and
serves the checked-in artifact bundle.

The borrower frontend is implemented in `frontend/` and includes the landing
page, assessment flow, processing state, results rendering, score sharing, and
API submission to `/api/score`. The current visual direction is a trust-first
minimal dark interface with oversized editorial typography, glassmorphism
surfaces, a slow blue/teal ambient canvas field, stripped-back feature/spec
sections, and cleaner assessment/results panels. The evaluator dashboard
currently exists as a health-backed shell and still needs complete
analytics-panel wiring.

The leading production-track candidate is a governed monotonic `XGBoost`
system that has passed monotonic, counterfactual, fairness, calibration, and
promotion-review checks in the offline governed comparison workflow. It has
**not yet been promoted** into the checked-in runtime bundle. The checked-in
runtime remains the calibrated stacking ensemble.

## What Is Stable

- Manifest-backed backend startup
- Checked-in runtime artifact bundle under `models/`
- Score, health, and analytics API contracts
- Borrower assessment and results flow
- Backend and pipeline test layout
- Governed monotonic-tree evaluation pipeline
- Fairness-hardening review workflow for the leading `XGBoost` candidate

## What Remains Open

- Dashboard endpoint wiring and panel UX are incomplete.
- Frontend-focused test coverage still needs expansion.
- Deployment assets such as Docker files are still placeholders or absent.
- Final production promotion of the monotonic `XGBoost` candidate into the
  checked-in runtime bundle has not been executed yet.
- `/api/debug-score` endpoint needs production security.

## Known Current Issues

- Python `3.12.x` is the supported local setup target; Python `3.14.x` is not.
- The frontend build can emit a non-critical bundle-size warning because the
  dashboard and results still include Recharts/R3F chunks.
- Some deployment directories remain scaffolding only and are not yet
  production-ready assets.

## Immediate Next Steps

1. Execute P0 audit findings (risk band alignment, debug endpoint security).
2. Decide on monotonic XGBoost promotion into the runtime bundle.
3. Wire the dashboard to the existing analytics endpoints.
4. Add deployment packaging once Track F is functional.
