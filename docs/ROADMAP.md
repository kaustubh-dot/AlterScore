# AlterScore Roadmap

## Roadmap Principles

- Contracts before implementation.
- Offline artifacts before online serving changes.
- Temporal-split validation before any promotion claims.
- Backend contract stability before frontend feature coupling.
- Report-backed analytics before dashboard visuals.
- Manifest-backed reproducibility before deployment packaging.

## Reality Check

The original PRD roadmap is ambitious and assumes a compressed end-to-end build. The repository has already completed a meaningful subset of that plan:

- Core backend/runtime foundation exists.
- Canonical feature registry exists.
- Synthetic data generation and validation exist.
- Local NLP extraction and persisted text PCA exist.
- Baseline and bounded classical training exist.
- Evaluation, fairness, PSI, percentiles, and global-importance artifacts exist.
- FastAPI score and analytics routes exist.
- A checked-in manifest-backed local serving bundle exists.

The remaining roadmap should therefore optimize for the actual dependency chain from the current codebase, not restart from the PRD's day-by-day classroom sequence.

## Program Tracks

### Track A - Governance Completion On Current Bundle

Goal:
Close the most important missing PRD governance items on top of the current logistic manifest-backed local bundle.

Status:

- Calibration-parity data is now included in the fairness artifact and `/api/fairness-report` contract.
- The individual-fairness proxy is now included for demographically different but psychometrically similar applicants.
- Fairness unit, artifact, and checked-in bundle smoke coverage now validate the richer payload.
- The richer detail is intentionally exposed through the fairness endpoint because the saved report is the API payload validated by the analytics schema.

Exit criteria:

- Fairness artifact includes demographic parity, equalized odds, calibration parity, and the individual-fairness proxy.
- Protected attributes remain audit-only.
- `/api/fairness-report` still serves a schema-valid payload from the startup-loaded bundle.

### Track B - Neural Offline Training

Goal:
Land the TabNet and MLP artifact paths as true offline jobs.

Status:

- TabNet training module (`backend/ml/training/neural/train_tabnet.py`) and CLI entrypoint (`scripts/training/train_tabnet.py`) are implemented.
- `pytorch-tabnet==4.1.0` added to `backend/requirements.txt`.
- `backend/ml/training/neural/__init__.py` package exists.
- 6 integration/smoke tests in `tests/integration/pipeline/test_tabnet_training.py` pass (full pipeline roundtrip, metrics merge, `.zip` save/load, import guard, temporal split integrity, missing file error).
- The module strictly reuses existing preprocessing, temporal-split, evaluation, and metrics infrastructure; no duplicate paths introduced.
- TabNet metrics merge cleanly into `metrics.json` and `population_percentiles.json` without breaking existing classical entries.

Remaining work:

- Implement residual MLP training module and script.
- ~~Implement residual MLP training module and script.~~ **Done.**
- ~~Add smoke tests for MLP path.~~ **Done (6/6 passing).**
- ~~Ensure MLP metrics also merge without breaking existing report consumers.~~ **Done.**

**Track B is complete. Both neural artifacts (TabNet .zip, MLP .pt) are implemented and tested.**

Exit criteria:

- Neural artifacts are saved reproducibly. ✅
- Test metrics are persisted without breaking current analytics readers. ✅
- Docs and experiment logs reflect the new artifact families. ✅

### Track C - Ensemble And Calibration

Goal:
Produce the first real production-candidate calibrated ensemble required by the PRD.

Remaining work:

- ~~Build stacking features from approved base-model outputs only.~~ **Done.**
- ~~Train the stacking ensemble without train/validation/test leakage.~~ **Done (meta-learner fitted on months 9-10 only).**
- ~~Calibrate on months `9-10` only.~~ **Done (isotonic `CalibratedClassifierCV`).**
- ~~Save uncalibrated and calibrated ensemble artifacts.~~ **Done (`.pkl` + config sidecar).**
- ~~Refresh metrics and percentile artifacts for the calibrated candidate.~~ **Done.**

**Track C is complete. 6/6 smoke tests pass. 93/93 total suite tests pass.**

Exit criteria:

- `calibrated_stacking.pkl` exists. ✅
- Evaluation reports include calibrated validation/test metrics. ✅
- The candidate is ready for explainability and manifest promotion review. ✅

### Track D - Production Explainability Refresh

Goal:
Refresh SHAP and counterfactual artifacts for the actual promoted model path rather than the current local logistic candidate.

Remaining work:

- Choose the production explainability path.
- Generate the refreshed persisted SHAP explainer.
- Generate SHAP summary output for inspection.
- Reconfirm counterfactual serving strategy for the calibrated candidate.
- Refresh global-importance outputs if the active serving model changes.

Exit criteria:

- Saved explainability artifacts deserialize from repo source.
- `/api/score` still returns meaningful explanation and action fields.
- Dashboard importance output matches the active serving model.

### Track E - Frontend Borrower Experience

Goal:
Implement the assessment-to-results borrower flow described in the PRD.

Remaining work:

- Add design tokens and visual direction.
- Add the full 27-question data model.
- Build landing page.
- Build assessment flow with telemetry capture.
- Build results page with score, SHAP factors, actions, eligibility, and tips.
- Build share/export flow.

Exit criteria:

- Full borrower flow works against the backend.
- Assessment submission generates a schema-valid score request.
- Results page renders the real API response cleanly on desktop and mobile.

### Track F - Frontend Evaluator Dashboard

Goal:
Implement the evaluator-facing analytics dashboard using the existing report-backed endpoints.

Remaining work:

- Build dashboard data hooks and panel loading/error handling.
- Build model comparison, fairness, drift, and importance sections.
- Build score-distribution and curve panels.
- Add responsive/mobile behavior.

Exit criteria:

- Dashboard loads all existing analytics endpoints.
- One failing endpoint does not collapse the full dashboard.
- Charts and tables remain usable at mobile widths.

### Track G - Deployment And Demo Readiness

Goal:
Package the application cleanly for local demo and later cloud deployment.

Remaining work:

- Add Docker assets.
- Document container startup for the manifest-backed bundle.
- Add release/rollback guidance for manifest changes.
- Run final smoke checks for backend, frontend, and bundle health.

Exit criteria:

- Local container run path is documented and repeatable.
- Manifest rollback steps are explicit.
- Demo checklist is complete.

## Recommended Execution Order

The most efficient order from the current repository state is:

1. Neural training foundation.
2. Ensemble and calibration.
3. Explainability refresh for the final candidate.
4. Manifest promotion review for the calibrated candidate.
5. Borrower frontend flow.
6. Evaluator dashboard.
7. Deployment packaging and demo polish.

## Detailed Next Milestones

| Milestone | Theme | Main Deliverables | Dependencies | Verification |
|---|---|---|---|---|
| M5.1 | Governance completion | Calibration-parity detail, individual-fairness proxy, refreshed fairness tests | Current fairness artifact foundation | Fairness artifact loads, tests pass, protected fields stay out of model inputs |
| M5.2 | Neural foundation | TabNet artifact, MLP artifact, metrics integration, experiment logs | Current preprocessing/training/report structure | Neural smoke tests pass and reports stay readable |
| M5.3 | Ensemble candidate | Stacking artifact, calibrated ensemble artifact, refreshed metrics and percentiles | M5.2 plus classical suite | Ensemble/calibration smoke tests pass and metrics are persisted |
| M5.4 | Explainability refresh | Refreshed SHAP explainer, SHAP summary output, production-candidate counterfactual decision | M5.3 | Score-time explainability stays schema-valid and non-trivial |
| M5.5 | Bundle promotion review | Candidate-vs-current comparison, manifest update decision, registry/docs refresh | M5.4 | Manifest-backed startup succeeds for the chosen candidate |
| M6.1 | Borrower UI foundation | Design tokens, question data, landing page, assessment shell | Stable score API contract | Frontend tests pass for navigation and payload construction |
| M6.2 | Borrower results flow | Results page, factor bars, actions, eligibility, share/export | M6.1 | Assessment-to-results flow passes locally |
| M6.3 | Evaluator dashboard | Dashboard panels for model stats, fairness, drift, importance, and curves | Stable analytics endpoints | Dashboard loads all major panels with loading/error states |
| M7.1 | Deployment packaging | Docker assets, startup docs, manifest rollback guidance | Backend and frontend stability | Health and scoring smoke checks pass in packaged flow |

## Detailed Task Map By Area

### Backend / Serving

- Keep the manifest-backed loader as the default startup path.
- Use direct runtime-model loading only for intentional dev/test overrides.
- Add hardening tests around manifest tamper and checksum mismatch behavior.
- Revisit health payload fields only when frontend needs more operational detail.

### ML / Offline

- Finish fairness detail first because it improves governance without changing the active serving model.
- Move next to TabNet and MLP so the ensemble track has real inputs.
- Do not start ensemble promotion until neural artifacts and their reports exist.
- Treat every meaningful training run as an experiment that updates both registry and log docs.

### Frontend

- Keep borrower flow ahead of dashboard polish.
- Tie question data directly to the PRD and score contract.
- Build charts only after the corresponding analytics payload is stable and tested.

### Testing

- Expand along the same dependency path as implementation.
- Prefer smoke coverage for new offline jobs first, then richer integration tests.
- Keep checked-in bundle smoke tests healthy after every artifact/manifest change.

### Docs

- Update `CURRENT_STATE`, `TODO`, and `ROADMAP` after milestone movement.
- Update contracts when response shapes change.
- Update model/deployment docs whenever the serving bundle changes.

## PRD Mapping

This roadmap maps back to the PRD sections as follows:

- PRD Sections 8 and 13.1:
  Governance completion and fairness/drift test expansion.
- PRD Section 7:
  Neural training, stacking, calibration, SHAP, DICE, metrics, and PSI.
- PRD Section 9:
  Backend hardening and serving behavior.
- PRD Section 10:
  Borrower assessment/results pages and evaluator dashboard.
- PRD Section 12:
  Overall build order, now translated into the repository's actual current state.

## Recommended Next Session

The most valuable bounded next session is:

1. Implement the stacking ensemble training module (`backend/ml/training/ensemble/train_stacking.py`, `scripts/training/train_stacking.py`).
2. The stacking module takes validation-split probability outputs from all 6 base models (logistic, RF, XGBoost, LightGBM, TabNet, MLP) and fits a logistic meta-learner on months 9-10 only, then applies isotonic calibration.
3. After `calibrated_stacking.pkl` exists, refresh the SHAP global importance, DICE, and fairness artifacts, and promote the ensemble via a manifest update.
