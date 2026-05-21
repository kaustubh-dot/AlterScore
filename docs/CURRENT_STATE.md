# Current State

**Date:** May 22, 2026
**Phase:** Repository stabilization before scoring/debugging audit
**Active Runtime:** Calibrated stacking ensemble v0.2.0
**Branch:** `main`

## Status Summary

The backend is implemented and should be treated as frozen for routine product
work during this cleanup phase. The default startup path is the repository-root
command `python -m uvicorn backend.app.main:app`, which loads
`models/registry/production_manifest.json`, validates manifest checksums, and
serves the checked-in artifact bundle.

The borrower frontend is implemented in `frontend/` and includes the landing
page, assessment flow, processing state, results rendering, score sharing, and
API submission to `/api/score`. The evaluator dashboard currently exists as a
health-backed shell and still needs complete analytics-panel wiring.

## What Is Stable

- Manifest-backed backend startup
- Checked-in runtime artifact bundle under `models/`
- Score, health, and analytics API contracts
- Borrower assessment and results flow
- Backend and pipeline test layout

## What Remains Open

- Scoring logic audit is still pending.
- Model behavior and score calibration are still under investigation.
- Dashboard endpoint wiring and panel UX are incomplete.
- Frontend-focused test coverage still needs expansion.
- Deployment assets such as Docker files are still placeholders or absent.

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

1. Finish the scoring/debugging audit without changing unrelated runtime docs again.
2. Add focused frontend tests for question data, payload assembly, retry behavior, and result rendering.
3. Wire the dashboard to the existing analytics endpoints with independent panel states.
4. Add deployment packaging once Track F is functional.
