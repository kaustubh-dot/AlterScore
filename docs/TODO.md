# AlterScore TODO

## Current Phase

The repository now has a stable backend foundation plus a checked-in manifest-backed local serving bundle for the current logistic runtime candidate. The immediate goal is no longer "make the backend run at all"; it is to close the largest PRD-to-implementation gaps in a deliberate order:

1. Resume the offline production-model track: neural models, stacking, calibration, and refreshed evaluation artifacts.
2. Build the borrower-facing frontend flow against the now-stable backend contracts.
3. Build the evaluator dashboard against the saved analytics endpoints and artifacts.
4. Add deployment packaging and final demo-readiness checks.

## Active Planning Assumptions

- Preserve the canonical 35 model inputs.
- Keep protected attributes audit-only.
- Keep `cohort_month` and `application_date` out of model inputs.
- Keep all heavy ML training offline-only.
- Treat the checked-in logistic bundle as the current validated local serving bundle, not the final promoted production model.
- Prefer small, test-backed increments that keep the manifest-backed startup path healthy.

## Immediate Priority Queue

- [x] Extend the persisted fairness artifact with calibration-parity detail.
- [x] Implement the individual-fairness proxy described in the PRD for psychometrically similar but demographically different pairs.
- [x] Refresh fairness tests and API contract coverage for the richer fairness payload.
- [ ] Decide whether the current lightweight persisted counterfactual contract remains the long-term serving interface or becomes a bridge to a fuller `dice_ml` artifact.
- [ ] Add a short design note or ADR if the future counterfactual direction changes materially from the current manifest-backed bundle.

## Detailed Execution Queue

### 1. Governance Completion On Current Bundle

- [x] Add calibration-parity computation to `backend/ml/evaluation/fairness.py`.
- [x] Add the individual-fairness proxy to `backend/ml/evaluation/fairness.py`.
- [x] Expand `models/reports/fairness_report.json` generation to carry the additional sections needed by the PRD.
- [x] Update analytics schemas and docs for the richer `/api/fairness-report` payload.
- [x] Add unit coverage for the new fairness calculations.
- [x] Add integration coverage proving the refreshed fairness artifact still loads cleanly through the manifest-backed bundle.

### 2. Neural Model Track

- [x] Create the offline TabNet training module and script path.
- [ ] Create the offline residual MLP training module and script path.
- [x] Ensure deterministic seed handling for both neural paths (TabNet done; MLP pending).
- [x] Add smoke tests that prove TabNet artifacts can be trained on the documented temporal split without leaking validation/test data.
- [ ] Add smoke tests for the MLP path.
- [x] Merge TabNet neural metrics into the existing report structure without breaking current analytics consumers.
- [ ] Merge MLP metrics the same way.
- [ ] Update `docs/MODEL_REGISTRY.md` and `docs/EXPERIMENT_LOG.md` when the first neural runs exist (TabNet experiment logged as EXP-20260515-008; MLP pending).

### 3. Ensemble And Calibration Track

- [ ] Implement stacking feature generation from the approved base-model set only.
- [ ] Prevent split leakage by ensuring the meta-learner sees only approved train/validation outputs.
- [ ] Add the calibration job for months `9-10` only.
- [ ] Save `models/artifacts/stacking_uncalibrated.pkl`.
- [ ] Save `models/artifacts/calibrated_stacking.pkl`.
- [ ] Refresh `models/reports/metrics.json` with ensemble validation/test metrics, thresholds, and calibration details.
- [ ] Update `models/reports/population_percentiles.json` for the calibrated production candidate.
- [ ] Decide when the manifest should switch from the logistic local candidate to the calibrated ensemble bundle.

### 4. Explainability Refresh For Final Production Candidate

- [ ] Decide which production-facing model path owns SHAP for the final promoted bundle.
- [ ] Build the refreshed persisted SHAP explainer artifact for that path.
- [ ] Generate the SHAP summary plot artifact for human review.
- [ ] Revisit the DICE/persisted-counterfactual strategy after the calibrated ensemble exists.
- [ ] Regenerate `models/reports/global_importance.json` if the active serving model changes.
- [ ] Add regression tests proving the refreshed explainability artifacts still deserialize from repository source.

### 5. Backend Hardening After Model Refresh

- [ ] Switch the checked-in manifest to the calibrated production candidate once that bundle is genuinely better and fully validated.
- [ ] Add one focused test proving manifest checksum failures surface clearly on copied or tampered bundles.
- [ ] Add one focused test proving manifest-backed health remains correct after the future ensemble promotion.
- [ ] Review `/api/health` and analytics payloads for any additional fields needed by the frontend dashboard.
- [ ] Add any missing backend contract tests before frontend implementation depends on new payload shapes.

### 6. Frontend Borrower Flow

- [ ] Add design tokens and lock the visual system for borrower-facing pages.
- [ ] Add PRD-faithful question data for the full 27-question assessment.
- [ ] Build the landing page.
- [ ] Build the assessment flow with sectioning, progress, validation, and retry-safe submission.
- [ ] Implement behavioral telemetry capture so it matches backend request expectations.
- [ ] Build the results page shell.
- [ ] Build the score gauge.
- [ ] Build SHAP factor bars and plain-language explanation rendering.
- [ ] Build counterfactual action rendering.
- [ ] Build loan-eligibility and improvement-tip presentation.
- [ ] Build the share-card / export path.

### 7. Frontend Evaluator Dashboard

- [ ] Build dashboard data hooks against the current analytics endpoints.
- [ ] Add loading and error states per panel so one failing endpoint does not break the whole page.
- [ ] Build model stats and baseline comparison tables.
- [ ] Build fairness, drift, and global-importance panels.
- [ ] Build score-distribution, ROC, PR, calibration, and confusion-matrix panels.
- [ ] Add responsive/mobile QA for dashboard tables and charts.

### 8. Testing Expansion

- [ ] Add broader integration coverage for the full data pipeline beyond generator validation and preprocessing split integrity.
- [ ] Add dedicated fairness artifact tests for calibration parity and the individual-fairness proxy.
- [ ] Add neural-model smoke tests.
- [ ] Add ensemble and calibration smoke tests.
- [ ] Add frontend unit/integration tests for assessment, results, and dashboard flows.
- [ ] Add E2E tests for assessment-to-results and dashboard loading.
- [ ] Add one local restart smoke test that proves the manifest-backed backend still reloads artifacts cleanly.

### 9. Deployment And Demo Readiness

- [ ] Add Docker files for backend and frontend.
- [ ] Define the local container startup path for the manifest-backed bundle.
- [ ] Document any model/runtime dependency constraints for the future ensemble bundle.
- [ ] Add a short release checklist for switching manifest versions safely.
- [ ] Run a final demo-readiness pass covering backend health, borrower flow, dashboard flow, and rollback guidance.

## Documentation Queue

- [ ] Update `docs/API_CONTRACTS.md` whenever fairness or analytics response shapes change.
- [ ] Update `docs/DATA_SCHEMA.md` only if feature definitions or exclusions change.
- [ ] Update `docs/MODEL_REGISTRY.md` after any new artifact family or serving-bundle promotion.
- [ ] Update `docs/EXPERIMENT_LOG.md` after every meaningful training run.
- [ ] Update `docs/DEPLOYMENT.md` when Docker or release steps land.
- [ ] Update `docs/CURRENT_STATE.md` after any milestone-level change in implementation status.
- [ ] Add ADRs under `docs/adr/` if the ensemble promotion path, fairness payload shape, or counterfactual strategy becomes materially more complex.

## Recommended Next Session Scope

If a future session wants the highest-value bounded task, start here:

1. Add the offline residual MLP training module and script path (`backend/ml/training/neural/train_mlp.py`, `scripts/training/train_mlp.py`).
2. Add deterministic smoke tests for the MLP path that keep the temporal split and protected-attribute exclusions intact.
3. Decide how to merge MLP metrics into `metrics.json` once both neural artifacts exist.
4. After both neural jobs exist, move to stacking feature generation (Track C).
