# AlterScore Roadmap

## Roadmap Principles

- Contracts before implementation.
- Offline artifacts before online serving changes.
- Temporal-split validation before any promotion claims.
- Backend contract stability before frontend feature coupling.
- Report-backed analytics before dashboard visuals.
- Manifest-backed reproducibility before deployment packaging.
- **Complete ALL backend serving work before frontend development begins.**

## Current Status Summary

| Track | Status | Notes |
|---|---|---|
| Track A — Governance | ✅ Complete | Fairness, calibration parity, individual-fairness proxy |
| Track B — Neural Training | ✅ Complete | TabNet + MLP, offline artifacts, 12 smoke tests |
| Track C — Ensemble & Calibration | ✅ Complete | Calibrated stacking ensemble, 6 smoke tests |
| Track D — Explainability & Promotion | ✅ Complete | SHAP, DICE, global importance, manifest promotion |
| Track D+ — Ensemble Serving Runtime | ✅ Complete | Adapter, loader, scoring, manifest, full validation |
| **Track E — Frontend Borrower Experience** | **🔲 Next** | Backend is fully complete; frontend can begin |
| Track F — Evaluator Dashboard | 🔲 Blocked on E | After Track E |
| Track G — Deployment & Demo | 🔲 Blocked on F | After Track F |

## Program Tracks

### Track A — Governance Completion (COMPLETE ✅)

Closed. Calibration parity, individual-fairness proxy, and fairness report refresh are all in the checked-in bundle.

### Track B — Neural Offline Training (COMPLETE ✅)

Closed. TabNet and MLP training modules, CLI entrypoints, and 12 integration smoke tests are all merged.

### Track C — Ensemble And Calibration (COMPLETE ✅)

Closed. `calibrated_stacking.pkl` exists with 6/6 smoke tests passing.

### Track D — Production Explainability Refresh (COMPLETE ✅)

Closed. SHAP, DICE, and global importance artifacts regenerated for the ensemble. Promotion pipeline (`promote_ensemble.py`) works end-to-end.

### Track D+ — Ensemble Serving Runtime (COMPLETE ✅)

Closed. The calibrated stacking ensemble is now the active production runtime model. All 6 base models load at startup, the ensemble adapter orchestrates the inference path, and all smoke tests pass with `stacking_ensemble` / `v0.2.0`.

**Key deliverables:**
- `backend/ml/inference/ensemble_adapter.py` — orchestrates base models → meta-features → meta-learner
- `WrappedEnsembleModel` — standard `predict_proba()` facade for DICE compatibility
- `artifact_loader.py` extended with `base_models` / `stacking_config` loading
- `scoring.py` routes through `predict_ensemble_proba()` when ensemble is active
- `production_manifest.json` declares `stacking_ensemble` with 6 base model checksums
- All 145 tests pass (unit + integration)

---

### Track E — Frontend Borrower Experience (NEXT)

Backend is unblocked. See `docs/FRONTEND_INTEGRATION_GUIDE.md` for API contracts.

**Phases:** E.1 Foundation → E.2 Assessment → E.3 Results → E.4 Polish

### Track F — Evaluator Dashboard (BLOCKED on E)

Blocked until Track E is complete. Analytics endpoints are stable and tested.

### Track G — Deployment & Demo (BLOCKED on F)

Blocked until Tracks E and F are complete.

---

## Recommended Execution Order

```
E.1 Foundation → E.2 Assessment → E.3 Results → E.4 Polish
  → F.1 Dashboard → F.2 Charts → F.3 Polish
    → G.1 Docker → G.2 Docs → G.3 Demo
```

## Milestones

| Milestone | Theme | Dependencies |
|---|---|---|
| M5.5 | Ensemble serving adapter + integration | ✅ Complete |
| M5.6 | Ensemble manifest promotion + validation | ✅ Complete |
| M6.1 | Borrower UI foundation | Backend complete |
| M6.2 | Borrower results flow | M6.1 |
| M6.3 | Evaluator dashboard | M6.2 |
| M7.1 | Deployment packaging | M6.3 |

## Known Technical Debt

- Stacking config sidecar still says `cv: "prefit"` — should say `FrozenEstimator` (cosmetic)
- `promote_ensemble.py` `code_ref` defaults to `"antigravity/dev"` — should use current branch
- Individual fairness proxy has a high flagged pair share (73%) — investigate if this is a scoring calibration issue
- Docker assets do not exist yet — Track G
- PyTorch/TabNet are currently required at startup for base model loading — consider lazy loading

## PRD Mapping

| PRD Section | Track |
|---|---|
| Sections 8, 13.1 | Track A (governance) — Complete |
| Section 7 | Tracks B, C, D (ML pipeline) — Complete |
| Section 9 | Track D+ (serving runtime) — Complete |
| Section 10 | Tracks E, F (frontend) — Next |
| Section 12 | Track G (deployment) — Blocked |
