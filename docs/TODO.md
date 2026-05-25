# AlterScore TODO

## Completed Backend Scope

- [x] Track A governance: fairness, calibration parity, individual-fairness proxy.
- [x] Track B neural training: TabNet and residual MLP.
- [x] Track C ensemble and calibration: calibrated stacking ensemble.
- [x] Track D explainability and promotion: SHAP, DICE, global importance, manifest promotion.
- [x] Track D+ runtime serving: ensemble adapter, loader integration, score routing, manifest-backed validation.
- [x] API endpoints: health, score, and report-backed analytics.
- [x] Checked-in runtime bundle: model artifacts, preprocessors, explainers, reports, manifest.

## Completed Frontend Scope

- [x] React/Vite app with routes for `/`, `/assessment`, `/results`, and `/dashboard`.
- [x] Landing experience with trust-first minimal dark/glass visual direction.
- [x] Assessment question data aligned to the backend score contract.
- [x] Answer renderers for number, MCQ, binary choice, Likert, and open text.
- [x] Behavioral telemetry capture and score payload construction.
- [x] Retry-safe score submission without clearing saved answers.
- [x] Processing screen and persisted results handoff.
- [x] Results page with animated score reveal, SHAP bars, counterfactual actions, eligibility, tips, and sharing/export.
- [x] Initial evaluator dashboard shell with backend health check.

## Current Frontend TODO

### Track E - Borrower QA And Tests

- [ ] Run browser screenshot QA for landing, assessment, processing, and results.
- [ ] Verify mobile layout at 375px and common desktop widths.
- [ ] Add tests for `frontend/src/data/questions.js`.
- [ ] Add tests for `frontend/src/services/scorePayload.js`.
- [ ] Add tests for retry-safe assessment submission.
- [ ] Add tests for results rendering with a mocked score response.
- [ ] Review R3F bundle size and decide whether manual chunking is needed.
- [ ] Screenshot QA the trust-first minimal/glass direction on desktop and mobile.

### Track F - Evaluator Dashboard

- [ ] Build dashboard API helpers for all analytics endpoints.
- [ ] Add independent loading/error/success state per dashboard panel.
- [ ] Implement model metrics and baseline comparison panels.
- [ ] Implement global importance and score distribution visualizations.
- [ ] Implement ROC, PR, calibration, and confusion-matrix visualizations.
- [ ] Implement fairness and drift panels.
- [ ] Add mobile overflow handling for charts and tables.
- [ ] Add dashboard tests with mocked endpoint payloads.

## Backend Future Enhancements

- [ ] Add a focused test for manifest checksum tamper detection.
- [ ] Add a focused test for manifest-backed health after future promotions.
- [ ] Review `/api/health` for any additional fields needed by the dashboard.
- [ ] Decide whether to keep the lightweight persisted counterfactual artifact contract or migrate to a fuller `dice_ml` object.
- [ ] Investigate lazy-loading PyTorch/TabNet base models to reduce cold start time.

## Deployment TODO

- [ ] Backend Dockerfile.
- [ ] Frontend Dockerfile.
- [ ] `docker-compose.yml`.
- [ ] Release smoke-test checklist.
- [ ] Demo walkthrough script.
- [ ] Rollback checklist tied to manifest versions.

## Cleanup TODO

- [ ] Remove or repair local restricted `runtime/pytest-*` directories outside version control if they continue to interfere with local tools.
- [ ] Keep generated frontend `dist/`, local virtualenvs, caches, and logs ignored and out of commits.
