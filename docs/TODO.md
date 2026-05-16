# AlterScore TODO

## Backend Status

All backend ML tracks (A–D) are complete. The runtime bundle is stable on `logistic_regression` v0.1.0 with `scikit-learn >=1.8.0`. All 93+ tests pass. The manifest, checksums, explainers, and reports are synchronized.

### Completed Backend Items

- [x] Implement calibration-parity computation in `backend/ml/evaluation/fairness.py`.
- [x] Implement the individual-fairness proxy for psychometrically similar but demographically different pairs.
- [x] Expand `models/reports/fairness_report.json` with calibration parity and individual-fairness proxy sections.
- [x] Update analytics schemas for the richer `/api/fairness-report` payload.
- [x] Add fairness unit, artifact, and smoke test coverage.
- [x] Create offline TabNet training module and CLI script.
- [x] Create offline MLP training module and CLI script.
- [x] Add smoke tests for both neural paths (12 tests total).
- [x] Implement stacking ensemble with temporal split integrity.
- [x] Add isotonic calibration (`FrozenEstimator` + `CalibratedClassifierCV`).
- [x] Save calibrated stacking artifact and config sidecar.
- [x] Refresh SHAP, DICE, and global importance for production candidate.
- [x] Promote ensemble to manifest (offline complete; runtime reverted to logistic).
- [x] Fix test isolation for parallel execution (explicit `None` for unused paths).
- [x] Regenerate all artifacts for `scikit-learn >=1.8.0` compatibility.
- [x] Verify all 11 manifest checksums match on-disk artifacts.
- [x] Repository hygiene cleanup (README, docs, .gitignore, temp files).

### Open Backend Items

- [ ] Implement ensemble serving adapter (see `docs/BACKEND_RUNTIME_ARCHITECTURE.md`).
- [ ] Switch checked-in manifest to calibrated ensemble once the serving adapter exists.
- [ ] Add focused test for manifest checksum tamper detection.
- [ ] Add focused test for manifest-backed health after future ensemble promotion.
- [ ] Review `/api/health` for additional fields needed by frontend dashboard.
- [ ] Decide whether the lightweight persisted counterfactual contract remains long-term or migrates to full `dice_ml`.

---

## Frontend TODO

### Track E — Frontend Borrower Experience

#### E.1 Foundation
- [ ] Create design tokens (`frontend/src/styles/tokens.css`): colors, typography, spacing, shadows.
- [ ] Create question data model (`frontend/src/data/questions.js`): all 27 PRD questions with types, options, validation.
- [ ] Set up React Router: `/`, `/assessment`, `/results`, `/dashboard`.
- [ ] Build landing page with hero section and CTA.

#### E.2 Assessment Flow
- [ ] Build `QuestionCard` component for all question types (Likert, binary, numeric, text).
- [ ] Build `SectionProgress` component with PRD-defined question sections.
- [ ] Implement answer state management with validation.
- [ ] Implement behavioral telemetry capture (`useTelemetry` hook).
- [ ] Build submit handler that constructs the `/api/score` payload.
- [ ] Implement retry-safe submission (same payload on retry, no answer clearing).
- [ ] Implement error handling (422 field errors, 500 retry, 503 unavailable).

#### E.3 Results Page
- [ ] Build score gauge component (semicircular arc, 300–850 range, risk band colors).
- [ ] Build risk band display with color badge.
- [ ] Build percentile indicator ("Better than X% of applicants").
- [ ] Build SHAP factor bars (horizontal, positive=green/right, negative=red/left).
- [ ] Build counterfactual action cards with `plain_language` and `+X points` badge.
- [ ] Build loan eligibility section (band, amount range, description).
- [ ] Build improvement tips section.
- [ ] Build share/export flow (screenshot, PDF, or clipboard).

#### E.4 Polish
- [ ] Mobile responsive QA at 375px, 768px, 1024px.
- [ ] Loading states (skeleton screens during API call).
- [ ] Error boundaries for rendering failures.
- [ ] Unit tests for question data, telemetry, payload construction.
- [ ] Integration tests for assessment flow and results rendering.
- [ ] E2E test: complete assessment → results with real backend.

### Track F — Evaluator Dashboard

#### F.1 Foundation
- [ ] Build dashboard page layout with panel navigation.
- [ ] Create `useAnalytics` hook for endpoint fetching with loading/error/data states.
- [ ] Implement per-panel error isolation.

#### F.2 Panels
- [ ] Model stats table (`/api/model-stats`).
- [ ] Baseline comparison table (`/api/baseline-comparison`).
- [ ] Fairness audit panel (`/api/fairness-report`).
- [ ] Feature drift panel (`/api/drift-report`).
- [ ] Feature importance chart (`/api/global-importance`).
- [ ] Score distribution histogram (`/api/score-distribution`).
- [ ] ROC curve chart (`/api/roc-data`).
- [ ] PR curve chart (`/api/pr-curve`).
- [ ] Calibration curve chart (`/api/calibration-curve`).
- [ ] Confusion matrix visualization (`/api/confusion-matrix`).

#### F.3 Polish
- [ ] Mobile responsive QA for all panels.
- [ ] Horizontal scroll for tables at mobile widths.
- [ ] Chart resizing for narrow viewports.
- [ ] Unit tests for each panel with mock data.

---

## Deployment TODO

### Track G — Deployment & Demo Readiness

- [ ] Create `deploy/docker/backend.Dockerfile`.
- [ ] Create `deploy/docker/frontend.Dockerfile`.
- [ ] Create `deploy/docker/docker-compose.yml`.
- [ ] Add Docker HEALTHCHECK against `/api/health`.
- [ ] Document local container startup path.
- [ ] Document environment variables with defaults.
- [ ] Document manifest verification steps.
- [ ] Write rollback checklist for manifest changes.
- [ ] Write smoke test checklist (health, score, analytics).
- [ ] Add demo walkthrough script.
- [ ] Run final release-readiness pass.

---

## Testing TODO

- [ ] Add frontend unit tests for assessment, results, and dashboard flows.
- [ ] Add E2E tests for assessment-to-results and dashboard loading.
- [ ] Add one local restart smoke test proving manifest-backed backend reloads cleanly.
- [ ] Add broader integration coverage for the full data pipeline.

---

## Documentation TODO

- [ ] Update `docs/API_CONTRACTS.md` if fairness or analytics response shapes change.
- [ ] Update `docs/DATA_SCHEMA.md` only if feature definitions change.
- [ ] Update `docs/MODEL_REGISTRY.md` after any new artifact promotion.
- [ ] Update `docs/EXPERIMENT_LOG.md` after any meaningful training run.
- [ ] Update `docs/DEPLOYMENT.md` when Docker assets land.
- [ ] Update `docs/CURRENT_STATE.md` after any milestone-level change.
- [ ] Add ADRs under `docs/adr/` if ensemble promotion or counterfactual strategy changes materially.

---

## Recommended Next Session

1. Start Track E — Frontend Borrower Experience.
2. Create design tokens, question data, and landing page (Phase E.1).
3. Build the assessment flow with telemetry capture (Phase E.2).
4. Hook the assessment to the backend API and build the results page (Phase E.3).
