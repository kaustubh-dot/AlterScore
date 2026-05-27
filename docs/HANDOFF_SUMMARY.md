# Handoff Summary: Front-End UI Developer Focus

**Date:** May 27, 2026  
**Status:** Monotonic XGBoost v2 serving stable; Borrower flow and Evaluator dashboard fully implemented; ready for styling/UI iterations.  
**Target Audience:** UI Developers working on frontend design, responsiveness, and WebGL asset optimization.

## Backend Status

The backend service is stable and serves the manifest-backed `xgboost_monotonic_v2` model. All scoring endpoints and analytical reports are fully operational.
* **Production Manifest:** `models/registry/production_manifest.json`
* **Test AUC:** `0.7547` (governed with strict monotonicity constraints on key behavioral features)

## API Surface (Stable & Fully Operational)

- `GET /api/health` — System status, loaded models, and artifact diagnostics.
- `POST /api/score` — Primary borrower submission path (scores psychometrics & telemetry).
- `GET /api/model-stats` — General metrics.
- `GET /api/baseline-comparison` — Performance compared to simulated loan officer and baseline model.
- `GET /api/fairness-report` — Demographics fairness indicators.
- `GET /api/drift-report` — Feature population stability index (PSI) tables.
- `GET /api/global-importance` — Population-wide feature SHAP rankings.
- `GET /api/score-distribution` — Population score histogram ranges.
- `GET /api/roc-data` — ROC curve coordinate arrays.
- `GET /api/pr-curve` — Precision-Recall curve coordinate arrays.
- `GET /api/calibration-curve` — Reliability calibration curves.
- `GET /api/confusion-matrix` — 2x2 prediction outcome matrix (True Positive, False Positive, etc.).

## Frontend Status

### Completed & Wired
- **Borrower Flow**: Landing page, psychometrics assessment cards (coerced inputs, WPM trackers, and copy-paste warnings), processing ticker animation screen, and local results summary (score reveal gauge, SHAP explanation list, counterfactual suggestion actions, loan limits, and improvement tips).
- **Evaluator Dashboard**: All analytics panels (drift, fairness, curves, ROC/PR, percentiles, baseline comparison) are integrated with independent panel wrappers, localized async loaders, and boundary error views. The confusion matrix rendering is fully wired to `/api/confusion-matrix`.

### Next Recommended UI Tasks
1. **Layout & Responsiveness**: Verify CSS/overflow alignments at `375px` mobile, tablet, and widescreen viewports (particularly tables and charts in the Evaluator Dashboard).
2. **styling & Aesthetics**: Iterate on custom glassmorphism styles, ambient backdrops, transitions, and three.js/WebGL particle configurations.
3. **WebGL/Bundle Optimization**: Check WebGL bundle size warnings and assess whether further chunks can be optimized.

## Local Quick Start

You can launch both services concurrently from the repository root:

```powershell
.\scripts\setup\start_alterscore.ps1
```

Or start them manually in separate shells:

**Terminal 1 (Backend)**:
```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1
# Start server
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

**Terminal 2 (Frontend)**:
```powershell
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

- Frontend URL: `http://127.0.0.1:5173`
- Backend URL: `http://127.0.0.1:8000/api`
- Backend Docs: `http://127.0.0.1:8000/docs`

## Read Next

- [docs/SETUP.md](file:///c:/Kaustubh/Projects/AlterScore/docs/SETUP.md) — Step-by-step developer environment setup.
- [docs/frontend_architecture.md](file:///c:/Kaustubh/Projects/AlterScore/docs/frontend_architecture.md) — Modular frontend directory structure and layout shell architecture.
- [docs/frontend_handoff.md](file:///c:/Kaustubh/Projects/AlterScore/docs/frontend_handoff.md) — In-depth mapping of JSON structures, pacing boundaries, and telemetry parameters.

