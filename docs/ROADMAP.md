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
| Track D — Explainability & Promotion | ✅ Complete (offline) | SHAP, DICE, global importance; runtime reverted to logistic |
| **Track D+ — Ensemble Serving Runtime** | **🔧 In progress** | **Bridge training-complete → serving-complete** |
| Track E — Frontend Borrower Experience | 🔲 Blocked on D+ | After backend is fully complete |
| Track F — Evaluator Dashboard | 🔲 Blocked on D+ | After Track E |
| Track G — Deployment & Demo | 🔲 Blocked on D+ | After Track F |

## Program Tracks

### Track A — Governance Completion (COMPLETE ✅)

Closed. Calibration parity, individual-fairness proxy, and fairness report refresh are all in the checked-in bundle.

### Track B — Neural Offline Training (COMPLETE ✅)

Closed. TabNet and MLP training modules, CLI entrypoints, and 12 integration smoke tests are all merged.

### Track C — Ensemble And Calibration (COMPLETE ✅)

Closed. `calibrated_stacking.pkl` exists with 6/6 smoke tests passing.

### Track D — Production Explainability Refresh (COMPLETE ✅ offline)

Closed offline. SHAP, DICE, and global importance artifacts exist. The promotion pipeline (`promote_ensemble.py`) works. Runtime was promoted then reverted because the scoring service has no ensemble inference adapter.

---

### Track D+ — Ensemble Serving Runtime (IN PROGRESS 🔧)

**Goal:** Make the calibrated stacking ensemble the active production runtime model with full explainability, manifest verification, and test coverage.

**Branch:** `feature/ensemble-serving-runtime`

**The core problem:** The scoring service calls `model.predict_proba(preprocessed_35_features)` directly. The stacking meta-learner expects 6 base-model probability columns, not 35 preprocessed features. An inference adapter is required to bridge this gap.

#### Phase D+.1 — Ensemble Inference Adapter

| Task | Details |
|---|---|
| Create `backend/ml/inference/ensemble_adapter.py` | Orchestrate raw features → base model probabilities → meta-learner prediction |
| Handle 3 inference paths | sklearn (logistic/RF/XGB/LGBM), TabNet (`.predict_proba`), MLP (torch forward) |
| Create `WrappedEnsembleModel` | Expose `predict_proba(preprocessed_35)` for DICE compatibility |
| Unit tests | `tests/unit/ml/test_ensemble_adapter.py` — shape, correctness, determinism |

#### Phase D+.2 — Artifact Loader Extension

| Task | Details |
|---|---|
| Extend `LoadedArtifactBundle` | Add `base_models` and `stacking_config` fields |
| Extend manifest schema | Add optional `base_models` and `stacking_config` sections to `production_manifest.py` |
| Load base models when ensemble | When `runtime_model_type == "ensemble"`, load 6 base models with checksum verification |
| Load stacking config | Read `calibrated_stacking_config.json` and validate base model order |

#### Phase D+.3 — Scoring Service Integration

| Task | Details |
|---|---|
| Modify `_predict_repayment_probability` | Accept optional ensemble bundle; route through adapter |
| Modify `ScoringService.__init__` | Construct `EnsembleInferenceBundle` when base models are loaded |
| Verify SHAP compatibility | Surrogate LR on processed features — should work identically |
| Verify DICE via wrapped model | Pass `WrappedEnsembleModel` to DICE explainer |

#### Phase D+.4 — Explainability Refresh

| Task | Details |
|---|---|
| Verify SHAP explainer | Surrogate was trained on ensemble predictions → should be correct |
| Regenerate DICE explainer | Use `WrappedEnsembleModel` so DICE calls the full ensemble path |
| Verify global importance | Confirm ranking still matches active model |
| Verify fairness report | Confirm predictions match ensemble output |

#### Phase D+.5 — Manifest Promotion

| Task | Details |
|---|---|
| Run full artifact pipeline | If needed, regenerate all artifacts with current sklearn environment |
| Compute checksums | SHA256 for all 18+ artifacts (model + 6 base models + config + reports) |
| Write production manifest | `runtime_model_name: "stacking_ensemble"`, `base_models` section |
| Check-in artifacts | Commit the updated manifest and all artifact changes |

#### Phase D+.6 — Testing & Validation

| Task | Details |
|---|---|
| Ensemble adapter unit tests | Shape, correctness, error handling |
| Ensemble serving integration tests | Full request → ensemble → response path |
| Update smoke tests | Change assertions from `logistic_regression` to `stacking_ensemble` |
| Run full test suite | All 93+ existing tests must pass |
| Fresh-clone verification | Verify checksums and serving on clean state |

**Definition of done:**
- `production_manifest.json` declares `stacking_ensemble` with 6 base models
- `/api/health` reports `stacking_ensemble` as model name
- `/api/score` returns valid score, SHAP factors, and DICE actions through the ensemble path
- All existing + new tests pass
- All docs updated

---

### Track E — Frontend Borrower Experience (BLOCKED)

Blocked until Track D+ is complete. See `docs/FRONTEND_INTEGRATION_GUIDE.md` for API contracts.

**Phases:** E.1 Foundation → E.2 Assessment → E.3 Results → E.4 Polish

### Track F — Evaluator Dashboard (BLOCKED)

Blocked until Track E is complete. Analytics endpoints are stable and tested.

### Track G — Deployment & Demo (BLOCKED)

Blocked until Tracks E and F are complete.

---

## Recommended Execution Order

```
D+.1 Ensemble adapter → D+.2 Loader extension → D+.3 Scoring integration
  → D+.4 Explainability refresh → D+.5 Manifest promotion → D+.6 Testing
    → E.1 Foundation → E.2 Assessment → E.3 Results → E.4 Polish
      → F.1 Dashboard → F.2 Charts → F.3 Polish
        → G.1 Docker → G.2 Docs → G.3 Demo
```

## Milestones

| Milestone | Theme | Dependencies |
|---|---|---|
| M5.5 | Ensemble serving adapter + integration | Training artifacts, stacking config |
| M5.6 | Ensemble manifest promotion + validation | M5.5, explainability refresh |
| M6.1 | Borrower UI foundation | M5.6 (backend fully complete) |
| M6.2 | Borrower results flow | M6.1 |
| M6.3 | Evaluator dashboard | M6.2 |
| M7.1 | Deployment packaging | M6.3 |

## Known Technical Debt

- Stacking config sidecar still says `cv: "prefit"` — should say `FrozenEstimator` (cosmetic)
- `promote_ensemble.py` `code_ref` defaults to `"antigravity/dev"` — should use current branch
- Individual fairness proxy has a high flagged pair share (73%) — investigate if this is a scoring calibration issue after ensemble serving is live
- Docker assets do not exist yet — Track G

## PRD Mapping

| PRD Section | Track |
|---|---|
| Sections 8, 13.1 | Track A (governance) — Complete |
| Section 7 | Tracks B, C, D (ML pipeline) — Complete offline |
| Section 9 | Track D+ (serving runtime) — In progress |
| Section 10 | Tracks E, F (frontend) — Blocked |
| Section 12 | Track G (deployment) — Blocked |
