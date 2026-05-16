# AlterScore Roadmap

## Roadmap Principles

- Contracts before implementation.
- Offline artifacts before online serving changes.
- Temporal-split validation before any promotion claims.
- Backend contract stability before frontend feature coupling.
- Report-backed analytics before dashboard visuals.
- Manifest-backed reproducibility before deployment packaging.

## Current Status Summary

| Track | Status | Notes |
|---|---|---|
| Track A — Governance | ✅ Complete | Fairness, calibration parity, individual-fairness proxy |
| Track B — Neural Training | ✅ Complete | TabNet + MLP, offline artifacts, 12 smoke tests |
| Track C — Ensemble & Calibration | ✅ Complete | Calibrated stacking ensemble, 6 smoke tests |
| Track D — Explainability & Promotion | ✅ Complete (offline) | SHAP, DICE, global importance; runtime reverted to logistic (see below) |
| Track E — Frontend Borrower Experience | 🔲 Not started | Next milestone |
| Track F — Evaluator Dashboard | 🔲 Not started | After Track E |
| Track G — Deployment & Demo | 🔲 Not started | After Track F |

**Why runtime uses logistic regression:** See `docs/BACKEND_RUNTIME_ARCHITECTURE.md`. The stacking ensemble expects 6 meta-features but the scoring service sends 35 raw features. A serving adapter is needed before re-promotion.

## Program Tracks

### Track A — Governance Completion (COMPLETE ✅)

Closed. Calibration parity, individual-fairness proxy, and fairness report refresh are all in the checked-in bundle.

### Track B — Neural Offline Training (COMPLETE ✅)

Closed. TabNet and MLP training modules, CLI entrypoints, and 12 integration smoke tests are all merged.

### Track C — Ensemble And Calibration (COMPLETE ✅)

Closed. `calibrated_stacking.pkl` exists with 6/6 smoke tests passing. Metrics and percentiles are merged.

### Track D — Production Explainability Refresh (COMPLETE ✅)

Closed (offline). SHAP, DICE, and global importance artifacts are regenerated and validated. Runtime was promoted then reverted — the promotion pipeline works, but serving requires the ensemble adapter documented in `BACKEND_RUNTIME_ARCHITECTURE.md`.

---

### Track E — Frontend Borrower Experience

**Goal:** Implement the full assessment-to-results borrower flow described in the PRD.

**Required backend integrations:**
- `POST /api/score` — core scoring endpoint (stable, tested)
- `GET /api/health` — verify backend readiness before scoring

**Implementation phases:**

#### Phase E.1 — Foundation (Milestone M6.1)

| Task | Details |
|---|---|
| Design tokens | Colors, typography, spacing, border radii, shadows — define in `frontend/src/styles/tokens.css` |
| Question data model | Create `frontend/src/data/questions.js` with all 27 PRD questions, types, options, validation rules |
| Landing page | Hero section, CTA button, brief explanation of the assessment |
| Router setup | React Router: `/` (Landing), `/assessment` (Assessment), `/results` (Results), `/dashboard` (Dashboard) |

**Definition of done:** Landing page renders, router navigates between empty page shells.

#### Phase E.2 — Assessment Flow (Milestone M6.1)

| Task | Details |
|---|---|
| Question renderer | Component that renders different question types (Likert, binary, numeric, text) |
| Section progress | Group questions into PRD sections with a progress bar |
| Answer state management | `useState` or context for all 27 answers + validation state |
| Field validation | Required fields, range checks, Q27 length limit |
| Telemetry capture | Track response times, answer changes, session duration, scroll hesitation, typing speed |
| Submit handler | Build the `/api/score` request payload and POST it |
| Error handling | Network failure → retry button (same payload), 422 → field errors, 503 → service unavailable |

**Suggested component structure:**
```
frontend/src/
  components/assessment/
    QuestionCard.jsx         — renders one question with type-appropriate input
    SectionProgress.jsx      — progress indicator by section
    AssessmentForm.jsx       — orchestrates questions, validation, telemetry
    SubmitButton.jsx         — submit with loading state
  pages/
    AssessmentPage.jsx       — full assessment page layout
  hooks/
    useTelemetry.js          — captures behavioral signals during the session
    useAssessmentState.js    — manages answer state and validation
  data/
    questions.js             — 27 questions with metadata, options, validation
```

**Definition of done:** User completes all 27 questions, telemetry is captured, payload is submitted, results page receives the response.

#### Phase E.3 — Results Page (Milestone M6.2)

| Task | Details |
|---|---|
| Score gauge | Semicircular or arc gauge showing 300–850 score with risk band color |
| Risk band display | Label + color badge |
| Percentile indicator | "Better than X% of applicants" |
| SHAP factor bars | Horizontal bars (positive=green, negative=red) with `display_name` labels |
| Counterfactual actions | Cards with `plain_language` text and `+X points` badges |
| Loan eligibility | Band, amount range, description |
| Improvement tips | Cards with title and body text |
| Share/export | Screenshot or PDF export of results |

**Definition of done:** Results page renders all score response fields correctly on desktop and mobile (375px).

#### Phase E.4 — Polish & Testing

| Task | Details |
|---|---|
| Mobile responsive QA | 375px, 768px, 1024px breakpoints |
| Loading states | Skeleton screens during API call |
| Error boundaries | Graceful fallback for rendering failures |
| Unit tests | Question data, telemetry, payload construction |
| Integration tests | Assessment flow with mock API, results rendering |
| E2E test | Full flow against real backend |

**Definition of done:** All tests pass, mobile works, error states are handled.

---

### Track F — Evaluator Dashboard

**Goal:** Implement the evaluator-facing analytics dashboard using existing report-backed endpoints.

**Required backend integrations:**
- All `GET /api/*` analytics endpoints (12 endpoints, all stable and tested)

**Implementation phases:**

#### Phase F.1 — Dashboard Foundation (Milestone M6.3)

| Task | Details |
|---|---|
| Dashboard layout | Sidebar or tab navigation between panels |
| Data hooks | Custom hooks for each endpoint with loading/error/data states |
| Panel loading states | Skeleton loaders per panel |
| Error isolation | One failed endpoint doesn't crash the dashboard |

**Suggested component structure:**
```
frontend/src/
  components/dashboard/
    ModelStatsPanel.jsx         — table of model metrics
    BaselineComparisonPanel.jsx — comparison table
    FairnessPanel.jsx           — subgroup audit visualization
    DriftPanel.jsx              — PSI feature drift table/chart
    ImportancePanel.jsx         — feature importance bar chart
    ScoreDistributionPanel.jsx  — score histogram
    ROCPanel.jsx                — ROC curve chart
    PRCurvePanel.jsx            — PR curve chart
    CalibrationPanel.jsx        — calibration curve chart
    ConfusionMatrixPanel.jsx    — confusion matrix heatmap
  hooks/
    useAnalytics.js             — generic fetcher with loading/error/data
  pages/
    DashboardPage.jsx           — dashboard layout with panels
```

#### Phase F.2 — Charts & Visualizations

| Endpoint | Chart Type | Library Suggestion |
|---|---|---|
| `/api/model-stats` | Data table | HTML table or simple grid |
| `/api/baseline-comparison` | Data table | HTML table |
| `/api/fairness-report` | Grouped bar chart + data table | Recharts or Chart.js |
| `/api/drift-report` | Horizontal bar chart (PSI values) | Recharts |
| `/api/global-importance` | Horizontal bar chart (SHAP importance) | Recharts |
| `/api/score-distribution` | Histogram | Recharts |
| `/api/roc-data` | Line chart (FPR vs TPR) | Recharts |
| `/api/pr-curve` | Line chart (Recall vs Precision) | Recharts |
| `/api/calibration-curve` | Line chart (predicted vs observed) | Recharts |
| `/api/confusion-matrix` | 2×2 heatmap grid | Custom CSS grid |

#### Phase F.3 — Polish & Responsive

| Task | Details |
|---|---|
| Mobile tables | Horizontal scroll containers |
| Chart responsive | Charts scale to container width |
| 375px QA | All panels usable at mobile width |
| Tests | Mock API responses for each panel |

**Definition of done:** Dashboard loads all panels, each panel handles loading/error/data independently, mobile is usable.

---

### Track G — Deployment & Demo Readiness

**Goal:** Package the application for local demo and document the deployment path.

**Implementation phases:**

#### Phase G.1 — Docker

| Task | Details |
|---|---|
| `deploy/docker/backend.Dockerfile` | Python image + runtime deps + artifact bundle |
| `deploy/docker/frontend.Dockerfile` | Node build stage + nginx serve |
| `deploy/docker/docker-compose.yml` | Backend + frontend + network |
| Health check | Docker HEALTHCHECK against `/api/health` |

#### Phase G.2 — Release Documentation

| Task | Details |
|---|---|
| Startup guide | Full local Docker startup with `docker compose up` |
| Environment variables | All variables documented with defaults |
| Manifest verification | How to verify artifact checksums after deployment |
| Rollback checklist | Step-by-step to revert a manifest change |
| Smoke test checklist | Health, score, analytics spot checks |

#### Phase G.3 — Demo Polish

| Task | Details |
|---|---|
| Demo data | Pre-filled assessment for quick demo |
| Demo walkthrough | Step-by-step demo script |
| Release checklist | Final pre-merge verification |

**Definition of done:** `docker compose up` starts both services, health passes, scoring works, dashboard loads.

---

## Recommended Execution Order

```
E.1 Foundation → E.2 Assessment → E.3 Results → E.4 Polish
    → F.1 Dashboard Foundation → F.2 Charts → F.3 Polish
        → G.1 Docker → G.2 Docs → G.3 Demo
```

## Milestones

| Milestone | Theme | Main Deliverables | Dependencies |
|---|---|---|---|
| M6.1 | Borrower UI foundation | Design tokens, question data, landing page, assessment flow | Stable `/api/score` contract |
| M6.2 | Borrower results flow | Results page, SHAP bars, actions, eligibility, share | M6.1 |
| M6.3 | Evaluator dashboard | All analytics panels with loading/error states | Stable analytics endpoints |
| M7.1 | Deployment packaging | Docker, startup docs, rollback guide | M6.2 + M6.3 |
| M7.2 | Demo readiness | Demo script, release checklist | M7.1 |

## Known Technical Debt / Future Enhancements

### Ensemble Serving Adapter

The calibrated stacking ensemble is training-complete but cannot serve in production until a scoring adapter transforms raw features → base-model probabilities → meta-learner input. See `docs/BACKEND_RUNTIME_ARCHITECTURE.md` for the implementation plan.

### Future Runtime Promotion Strategy

1. Implement the ensemble serving adapter
2. Regenerate SHAP/DICE artifacts against the ensemble
3. Update manifest to point to `calibrated_stacking.pkl` with all base models
4. Update smoke test expectations for `stacking_ensemble` model name
5. Run full test suite
6. Promote

### Remaining Backend Hardening

- Add a focused test proving manifest checksum failures surface clearly on tampered bundles
- Add a focused test proving manifest-backed health remains correct after future promotions
- Review `/api/health` for additional fields needed by the frontend dashboard

### Deployment Gaps

- No Docker assets exist yet
- No CI/CD pipeline defined
- No production logging/monitoring infrastructure
- No secrets management for cloud deployment

### Scalability Considerations

- Scoring latency is currently 200–800ms per request (single process)
- For higher throughput, consider uvicorn workers, async preprocessing, or model caching
- The manifest loader is startup-only (models are cached in memory)
- Analytics endpoints are read-only from pre-computed JSON files — very fast

## Remaining Risks / Open Questions

1. **Chart library choice** — Recharts is suggested but not mandated. The dashboard should use whatever integrates best with the React scaffold.
2. **Q27 text input UX** — The PRD requires a text area for resilience text. Consider character count, placeholder text, and accessibility.
3. **Share/export mechanism** — The PRD mentions a share card. Implementation options: html2canvas screenshot, server-side PDF, or clipboard copy. Decision needed during Track E.
4. **Authentication** — Not in current scope. If needed later, add middleware in FastAPI and protected routes in React.
5. **Internationalization** — Not in current scope. Question text and UI labels are English-only.

## PRD Mapping

| PRD Section | Track |
|---|---|
| Sections 8, 13.1 | Track A (governance) — Complete |
| Section 7 | Tracks B, C, D (ML pipeline) — Complete |
| Section 9 | Backend hardening — Mostly complete |
| Section 10 | Tracks E, F (frontend) — Not started |
| Section 12 | Track G (deployment) — Not started |
