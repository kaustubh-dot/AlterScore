# AlterScore Roadmap

## Roadmap Principles

- Contracts before implementation.
- Offline artifacts before online serving changes.
- Temporal-split validation before promotion claims.
- Backend contract stability before frontend feature coupling.
- Report-backed analytics before dashboard visuals.
- Manifest-backed reproducibility before deployment packaging.

## Current Status Summary

| Track | Status | Notes |
|---|---|---|
| Track A - Governance | Complete | Fairness, calibration parity, individual-fairness proxy |
| Track B - Neural Training | Complete | TabNet + MLP, offline artifacts, smoke tests |
| Track C - Ensemble & Calibration | Complete | Calibrated stacking ensemble |
| Track D - Explainability & Promotion | Complete | SHAP, DICE, global importance, manifest promotion |
| Track D+ - Ensemble Serving Runtime | Complete | Adapter, loader, scoring, manifest-backed validation |
| Track D++ - Governed Constrained Trees | Complete | Monotonic XGBoost/LightGBM comparison and promotion gating |
| Track E - Borrower Frontend | Implemented, QA pending | Landing, assessment, submission, processing, results, sharing |
| Track F - Evaluator Dashboard | Pending | Dashboard shell exists; analytics panel wiring remains |
| Track G - Deployment & Demo | Pending | Docker/release assets after Track F |

## Program Tracks

### Track A - Governance Completion

Closed. Calibration parity, individual-fairness proxy, and fairness report
refresh are in the checked-in bundle.

### Track B - Neural Offline Training

Closed. TabNet and MLP training modules, CLI entrypoints, artifacts, and smoke
tests are merged.

### Track C - Ensemble And Calibration

Closed. `calibrated_stacking.pkl` exists and is promoted as the active runtime
meta-learner.

### Track D - Production Explainability Refresh

Closed. SHAP, DICE, and global importance artifacts were regenerated for the
ensemble. The promotion pipeline works end to end.

### Track D+ - Ensemble Serving Runtime

Closed. The backend loads the calibrated stacking ensemble, all six base models,
stacking config, preprocessor, text PCA, explainers, reports, and manifest
checksums at startup. `/api/score` routes through `predict_ensemble_proba()`.

### Track D++ - Governed Constrained Trees

Closed. Monotonic constrained-tree candidates were evaluated through the full
governance stack. Monotonic `XGBoost` is now the leading production candidate,
while TabNet remains research-only unless it clears the same governance gates
later.

### Track E - Borrower Frontend

Implementation is present. Remaining work is QA and test coverage:

- Browser screenshot QA for landing, assessment, processing, and results.
- Mobile checks at 375px and common desktop widths.
- Focused tests for question data, telemetry, score payloads, retry behavior,
  missing results state, and rendering of SHAP/action/eligibility blocks.
- Optional bundle optimization for the R3F vendor chunk if demo performance
  requires it.

### Track F - Evaluator Dashboard

Pending. The current dashboard shell checks backend health but still needs:

- Independent data hooks for all analytics endpoints.
- Loading, error, empty, and success states per panel.
- Model metrics, baseline, fairness, drift, global importance, score
  distribution, ROC, PR, calibration, and confusion-matrix views.
- Mobile table/chart overflow handling.

### Track G - Deployment & Demo

Pending until Track F is usable. Required deliverables:

- Backend Dockerfile.
- Frontend Dockerfile.
- `docker-compose.yml`.
- Release smoke-test checklist.
- Demo walkthrough script and rollback notes.

## Recommended Execution Order

```text
E.4 QA/tests
  -> F.1 dashboard data hooks
  -> F.2 dashboard panels
  -> F.3 dashboard responsive polish
  -> G.1 Docker packaging
  -> G.2 release docs
  -> G.3 demo script
```

## Milestones

| Milestone | Theme | Dependencies |
|---|---|---|
| M5.5 | Ensemble serving adapter + integration | Complete |
| M5.6 | Ensemble manifest promotion + validation | Complete |
| M6.1 | Borrower UI foundation | Complete |
| M6.2 | Borrower assessment/results flow | Complete, QA pending |
| M6.3 | Evaluator dashboard | Track E QA and frontend test harness |
| M7.1 | Deployment packaging | Dashboard usable |

## Known Technical Debt

- Stacking config sidecar still says `cv: "prefit"`; scikit-learn now represents this with `FrozenEstimator` semantics.
- `promote_ensemble.py` `code_ref` defaults to `"antigravity/dev"`; it should use the current branch or explicit release identifier.
- Individual fairness proxy has a high flagged-pair share; investigate before pilot claims.
- Docker assets do not exist yet.
- PyTorch/TabNet are currently required at startup for base-model loading; lazy loading may reduce cold start time.
- Frontend unit/E2E coverage is still thin for the borrower flow and dashboard.

## PRD Mapping

| PRD Section | Track |
|---|---|
| Sections 8, 13.1 | Track A governance - complete |
| Section 7 | Tracks B, C, D ML pipeline - complete |
| Section 9 | Track D+ serving runtime - complete |
| Section 10 | Track E borrower frontend implemented; Track F dashboard pending |
| Section 12 | Track G deployment - pending |
