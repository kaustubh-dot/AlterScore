# AlterScore TODO

## Completed Backend Scope

- [x] Track A governance: fairness, calibration parity, individual-fairness proxy.
- [x] Track B neural training: TabNet and residual MLP.
- [x] Track C ensemble and calibration: calibrated stacking ensemble.
- [x] Track D explainability and promotion: SHAP, DICE, global importance, manifest promotion.
- [x] Track D+ runtime serving: ensemble adapter, loader integration, score routing, manifest-backed validation.
- [x] Track D++ constrained-tree promotion: monotonic `XGBoost` is the checked-in manifest runtime.
- [x] API endpoints: health, score, debug-score for local use, and report-backed analytics.
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
- [x] Dashboard integration for health, metrics, baseline, fairness, drift, importance, score distribution, ROC, PR, and calibration.

## P0 - Runtime And Governance Alignment

- [ ] Reconcile checked-in monotonic runtime metrics with the governed full-run review metrics.
- [ ] Resolve, harden, or explicitly accept the checked-in fairness attention item for `gender=non_binary`.
- [ ] Regenerate/update promoted monotonic reports if the current checked-in reports are stale.
- [ ] Replace manifest `code_ref` historical labels with explicit branch/commit identifiers during the next promotion.

## Track E - Borrower QA And Tests

- [ ] Run browser screenshot QA for landing, assessment, processing, and results.
- [ ] Verify mobile layout at 375px and common desktop widths.
- [ ] Add tests for `frontend/src/data/questions.js`.
- [ ] Add tests for `frontend/src/services/scorePayload.js`.
- [ ] Add tests for retry-safe assessment submission.
- [ ] Add tests for results rendering with a mocked score response.
- [ ] Review R3F bundle size and decide whether manual chunking is needed.

## Track F - Evaluator Dashboard

- [ ] Render the `/api/confusion-matrix` response.
- [ ] Add independent loading/error/success state per dashboard panel.
- [ ] Add empty-state handling for missing analytics artifacts.
- [ ] Add dashboard tests with mocked endpoint payloads.
- [ ] Add dashboard tests for endpoint failure behavior.
- [ ] Add mobile overflow handling for charts and tables.
- [ ] Consider exposing runtime model name/type directly from `/api/health`.

## Release And Demo TODO

- [ ] Write a local/manual runbook for starting backend and frontend.
- [ ] Document production-style environment variables for a manual host.
- [ ] Validate clean local backend startup with the current manifest runtime.
- [ ] Validate clean local frontend build and API base URL configuration.
- [ ] Release smoke-test checklist.
- [ ] Demo walkthrough script.
- [ ] Rollback checklist tied to manifest versions.

## Cleanup TODO

- [x] Remove ignored `__pycache__`, generated reports, local logs, generated data, and restricted `runtime/pytest-temp` clutter from the workspace.
- [x] Keep generated frontend `dist/`, local virtualenvs, caches, and logs ignored and out of commits.
- [ ] Keep local dependency installs (`venv/`, `frontend/node_modules/`) ignored; remove manually only when reclaiming disk space.
