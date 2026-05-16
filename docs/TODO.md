# AlterScore TODO

## Completed — Track D+ (Ensemble Serving Runtime) ✅

Branch: `feature/ensemble-serving-runtime`

### Phase D+.1 — Ensemble Inference Adapter ✅
- [x] Create `backend/ml/inference/ensemble_adapter.py`
  - [x] `EnsembleInferenceBundle` dataclass
  - [x] `predict_ensemble_proba()` — preprocessed features → base probabilities → meta-learner
  - [x] `_predict_base_model_proba()` — handle sklearn, TabNet, and MLP inference
  - [x] `WrappedEnsembleModel` — `predict_proba(preprocessed_35)` facade for DICE
- [x] Create `tests/unit/ml/test_ensemble_adapter.py` (5 tests)

### Phase D+.2 — Artifact Loader Extension ✅
- [x] Extend `LoadedArtifactBundle` with `base_models` and `stacking_config` fields
- [x] Extend `production_manifest.py` with optional `base_models` and `stacking_config` schema
- [x] Load 6 base models when `runtime_model_type == "ensemble"` (joblib / TabNet / torch)
- [x] Load stacking config sidecar and validate base model order

### Phase D+.3 — Scoring Service Integration ✅
- [x] `ScoringService.__init__` constructs `EnsembleInferenceBundle` when base models are loaded
- [x] `_predict_repayment_probability` routes through `predict_ensemble_proba()` when ensemble
- [x] DICE receives `WrappedEnsembleModel` when ensemble is active

### Phase D+.4 — Explainability Refresh ✅
- [x] SHAP surrogate validated against ensemble predictions
- [x] DICE explainer regenerated
- [x] Global importance, fairness, PSI reports regenerated

### Phase D+.5 — Manifest Promotion ✅
- [x] Full artifact pipeline executed via `promote_ensemble.py`
- [x] SHA256 checksums computed for all 18 artifacts
- [x] `production_manifest.json` declares `stacking_ensemble` with `base_models` + `stacking_config`

### Phase D+.6 — Testing & Validation ✅
- [x] Ensemble adapter unit tests (5 passing)
- [x] Smoke tests updated for `stacking_ensemble` / `v0.2.0`
- [x] Full test suite: 145 passed, 0 failed

### Documentation Updates ✅
- [x] `CURRENT_STATE.md` — ensemble as active runtime
- [x] `ROADMAP.md` — Track D+ complete, Track E next
- [x] `TODO.md` — all D+ tasks checked
- [x] `BACKEND_RUNTIME_ARCHITECTURE.md` — updated for ensemble serving
- [x] `DEPLOYMENT.md` — updated artifact checklist for ensemble
- [x] `DECISIONS.md` — added DEC-0017 for ensemble serving
- [x] `README.md` — reflects ensemble serving
- [x] `MODEL_REGISTRY.md` — updated for ensemble runtime

---

## Backend Completion (Tracks A–D+)

### Completed Backend Items
- [x] All governance items (calibration parity, individual fairness, fairness report)
- [x] TabNet + MLP neural training (12 smoke tests)
- [x] Calibrated stacking ensemble training (6 smoke tests)
- [x] SHAP + DICE + global importance + fairness + PSI artifacts
- [x] Full promotion pipeline (`promote_ensemble.py`)
- [x] Phase 7: Model Training (Classical & TabNet/MLP)
- [x] Phase 8: Fairness & Metrics
- [x] Phase 9.1-9.2: API Endpoints (Health, Analytics)
- [x] Phase 9.3: Score Endpoint
- [x] **Track D+: Ensemble Serving Runtime & Explainability** (Completed)
- [x] Implement SHAP and DICE for Ensemble
- [x] Finalize backend architecture
- [x] Backend Feature Complete & Freeze

### Open Backend Items (Future Enhancements)
- [ ] Focused test for manifest checksum tamper detection
- [ ] Focused test for manifest-backed health after future promotions
- [ ] Review `/api/health` for additional fields needed by frontend dashboard
- [ ] Decide whether lightweight persisted counterfactual contract remains or migrates to full `dice_ml`
- [ ] Lazy-load PyTorch/TabNet at startup to reduce cold start time

---

## Frontend TODO (Unblocked)

### Track E — Frontend Borrower Experience
- [ ] E.1 Foundation (design tokens, question data, router, landing page)
- [ ] E.2 Assessment flow (question renderer, telemetry, submit handler)
- [ ] E.3 Results page (score gauge, SHAP bars, actions, eligibility)
- [ ] E.4 Polish (mobile, loading states, error handling, tests)

### Track F — Evaluator Dashboard
- [ ] F.1 Foundation (layout, data hooks, error isolation)
- [ ] F.2 Panels (10 analytics panels)
- [ ] F.3 Polish (mobile, responsive charts)

---

## Deployment TODO (Blocked Until E+F Complete)

### Track G — Deployment & Demo
- [ ] Docker assets (backend + frontend Dockerfiles, docker-compose)
- [ ] Release documentation (startup, env vars, rollback, smoke tests)
- [ ] Demo polish (walkthrough script, demo data, release checklist)
