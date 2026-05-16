# AlterScore TODO

## Active Work — Track D+ (Ensemble Serving Runtime)

Branch: `feature/ensemble-serving-runtime`

### Phase D+.1 — Ensemble Inference Adapter
- [ ] Create `backend/ml/inference/ensemble_adapter.py`
  - [ ] `EnsembleInferenceBundle` dataclass (stacking model, base models dict, model order, preprocessor, config)
  - [ ] `predict_ensemble_proba()` — transform preprocessed features → base probabilities → meta-learner prediction
  - [ ] `_predict_base_model_proba()` — handle sklearn, TabNet, and MLP inference paths
  - [ ] `WrappedEnsembleModel` — exposes `predict_proba(preprocessed_35)` for DICE compatibility
- [ ] Create `tests/unit/ml/test_ensemble_adapter.py`
  - [ ] Meta-feature matrix shape matches stacking model (1, 6)
  - [ ] Adapter produces valid probabilities for all base model types
  - [ ] Adapter is deterministic across repeated calls
  - [ ] Error handling for missing/corrupt base models

### Phase D+.2 — Artifact Loader Extension
- [ ] Extend `LoadedArtifactBundle` in `backend/app/core/artifact_loader.py`
  - [ ] Add `base_models: dict[str, Any] | None` field
  - [ ] Add `stacking_config: dict[str, Any] | None` field
- [ ] Extend `production_manifest.py`
  - [ ] Add optional `base_models` section to manifest schema
  - [ ] Add optional `stacking_config` entry to manifest schema
  - [ ] Validate base model checksums when present
- [ ] Update `_resolve_artifact_state` and `_build_manifest_paths`
  - [ ] When `runtime_model_type == "ensemble"`, resolve base model paths from manifest
  - [ ] Load each base model with checksum verification
  - [ ] Load stacking config sidecar and validate base model order
- [ ] Update artifact loading tests

### Phase D+.3 — Scoring Service Integration
- [ ] Modify `ScoringService.__init__` in `scoring.py`
  - [ ] If `artifacts.base_models is not None`, construct `EnsembleInferenceBundle`
  - [ ] Store as `self.ensemble_bundle`
- [ ] Modify `_predict_repayment_probability`
  - [ ] Accept optional `ensemble_bundle` parameter
  - [ ] Route through `predict_ensemble_proba()` when bundle is provided
- [ ] Verify SHAP compatibility (surrogate LR on processed features — should be unchanged)
- [ ] Wire DICE to use `WrappedEnsembleModel` when ensemble is active

### Phase D+.4 — Explainability Refresh
- [ ] Verify `shap_explainer.pkl` — confirm surrogate was trained on ensemble predictions
- [ ] Regenerate `dice_explainer.pkl` using `WrappedEnsembleModel`
- [ ] Verify `global_importance.json` matches active ensemble model
- [ ] Verify `fairness_report.json` predictions match ensemble output
- [ ] Verify `psi_report.json` is model-independent (no change expected)

### Phase D+.5 — Manifest Promotion
- [ ] Run full artifact pipeline (if regeneration needed)
- [ ] Compute SHA256 checksums for all artifacts (~18 files)
- [ ] Write `production_manifest.json` with:
  - [ ] `runtime_model_name: "stacking_ensemble"`
  - [ ] `runtime_model_type: "ensemble"`
  - [ ] `base_models` section with 6 entries
  - [ ] `stacking_config` entry
- [ ] Check-in updated manifest and artifacts
- [ ] Update `metrics_summary` with ensemble test metrics

### Phase D+.6 — Testing & Validation
- [ ] Create `tests/integration/pipeline/test_ensemble_serving.py`
  - [ ] Load manifest-backed ensemble bundle
  - [ ] Score a valid request through the ensemble adapter
  - [ ] Verify score is in 300–850 range
  - [ ] Verify SHAP explanations are non-empty
  - [ ] Verify DICE actions are non-empty
  - [ ] Verify health reports `stacking_ensemble` as model name
- [ ] Update `tests/integration/api/test_checked_in_runtime_bundle_smoke.py`
  - [ ] Change model name assertions from `logistic_regression` to `stacking_ensemble`
  - [ ] Change model version assertions
  - [ ] Add base model loading assertions
- [ ] Run full test suite — all 93+ existing tests must pass
- [ ] Verify fresh-clone checksums

---

## Documentation Updates (After D+ Complete)

- [ ] Update `CURRENT_STATE.md` — reflect ensemble as active runtime
- [ ] Update `ENGINEERING_CONTEXT.md` — describe ensemble serving architecture
- [ ] Update `MODEL_REGISTRY.md` — document ensemble promotion event
- [ ] Update `DECISIONS.md` — add DEC-0017 for ensemble serving adapter
- [ ] Update `DEPLOYMENT.md` — update artifact checklist for ensemble
- [ ] Update `BACKEND_RUNTIME_ARCHITECTURE.md` — mark adapter as implemented
- [ ] Update `README.md` — reflect ensemble serving
- [ ] Update `TESTING_STRATEGY.md` — add ensemble serving test section

---

## Backend Completion (After D+)

### Completed Backend Items (Tracks A–D)
- [x] All governance items (calibration parity, individual fairness, fairness report)
- [x] TabNet + MLP neural training (12 smoke tests)
- [x] Calibrated stacking ensemble training (6 smoke tests)
- [x] SHAP + DICE + global importance + fairness + PSI artifacts
- [x] Full promotion pipeline (`promote_ensemble.py`)
- [x] Manifest-backed startup with SHA256 verification
- [x] All analytics endpoints (12 tested)
- [x] Test isolation for parallel execution
- [x] scikit-learn 1.8.0 compatibility
- [x] Repository hygiene cleanup

### Open Backend Items (Beyond D+)
- [ ] Focused test for manifest checksum tamper detection
- [ ] Focused test for manifest-backed health after future promotions
- [ ] Review `/api/health` for additional fields needed by frontend dashboard
- [ ] Decide whether lightweight persisted counterfactual contract remains or migrates to full `dice_ml`

---

## Frontend TODO (Blocked Until D+ Complete)

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

---

## Recommended Next Session

1. Implement Phase D+.1 — Ensemble Inference Adapter
2. Write unit tests for the adapter
3. Verify adapter works with all 6 base model types
