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

## Completed Pre-Pilot & Release Hardening

- [x] Reconcile checked-in monotonic runtime metrics with the governed full-run review metrics.
- [x] Resolve, harden, or explicitly accept the checked-in fairness attention item for `gender=non_binary`.
- [x] Replace manifest `code_ref` historical labels with explicit branch/commit identifiers during the next promotion (Locked to `"main"`).
- [x] Add tests for questions and scoring payload construction (`questions.test.js`, `scorePayload.test.js`, and `run-tests.js`).
- [x] Render the `/api/confusion-matrix` response.
- [x] Add independent loading/error/success state per dashboard panel (Createdized async `PanelWrapper` with error boundary limits).
- [x] Write a local/manual runbook for starting backend and frontend (`docs/DEPLOYMENT_RUNBOOK.md`).
- [x] Create automated process runner script (`scripts/setup/start_alterscore.ps1`).
- [x] Validate clean local frontend build and API base URL configuration.

## Track E - Borrower QA And Remaining Layout Checks

- [x] Run browser screenshot QA for landing, assessment, processing, and results.
- [x] Verify mobile layout at 375px and common desktop widths (implemented session resets and grouped controls beautifully).
- [ ] Review R3F bundle size and decide whether manual Rollup chunking is needed to split large three.js assets.

## Track F - Evaluator Dashboard & Minor Mock Coverage

- [x] Add dashboard unit tests with mocked endpoint payloads.
- [x] Add dashboard tests for endpoint failure behavior.
- [ ] Add mobile overflow handling for charts and tables.

## Release And Demo Walkthroughs

- [x] Release smoke-test checklist.
- [x] Demo walkthrough script (documented in walkthrough.md and verified).
- [ ] Rollback checklist tied to manifest versions.

## Cleanup TODOs

- [x] Remove ignored `__pycache__`, generated reports, local logs, generated data, and restricted `runtime/pytest-temp` clutter from the workspace.
- [x] Keep generated frontend `dist/`, local virtualenvs, caches, and logs ignored and out of commits.
- [x] Keep local dependency installs (`venv/`, `frontend/node_modules/`) ignored; remove manually only when reclaiming disk space.
