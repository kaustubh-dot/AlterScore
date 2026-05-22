# Current State

**Date:** May 22, 2026
**Phase:** Governed production-candidate stabilization
**Active Runtime:** Checked-in calibrated stacking ensemble baseline
**Leading Candidate:** Monotonic `XGBoost`
**Branch:** `codex/constrained-tree-production`

## Status Summary

The backend is implemented and manifest-backed. The default startup path is the
repository-root command `python -m uvicorn backend.app.main:app`, which loads
`models/registry/production_manifest.json`, validates manifest checksums, and
serves the checked-in artifact bundle.

The borrower frontend is implemented in `frontend/` and includes the landing
page, assessment flow, processing state, results rendering, score sharing, and
API submission to `/api/score`. The evaluator dashboard currently exists as a
health-backed shell and still needs complete analytics-panel wiring.

The leading production-track candidate is now a governed monotonic `XGBoost`
system that has passed monotonic, counterfactual, fairness, calibration, and
promotion-review checks in the current offline governed comparison workflow.

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

## Known Current Issues

- Python `3.12.x` is the supported local setup target; Python `3.14.x` is not.
- A fresh backend dependency install in this synced Windows workspace resolved
  dependencies successfully but hit a local file-lock error inside the temporary
  virtual environment during package installation.
- The frontend build can emit a non-critical bundle-size warning because of the
  WebGL/R3F stack.
- Some deployment directories remain scaffolding only and are not yet
  production-ready assets.

## Immediate Next Steps

1. Finalize release packaging and promotion-review handoff for the monotonic `XGBoost` candidate.
2. Add focused frontend tests for question data, payload assembly, retry behavior, and result rendering.
3. Wire the dashboard to the existing analytics endpoints with independent panel states.
4. Add deployment packaging once Track F is functional.
