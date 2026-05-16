# Handoff Summary: Backend Freeze & Frontend Transition

**Date:** May 2026  
**Status:** Backend FROZEN — Architecture v0.2.0  
**Target Audience:** Frontend/Full-Stack Developer taking over Track E

---

## 1. Backend Status: FROZEN

The backend architecture, API endpoints, ML models, explainability tools (SHAP/DICE), and artifact management systems are **FROZEN**. Do not attempt to add features, retrain models, or modify `production_manifest.json` without explicit architectural review.

### What MUST NOT Be Changed
- Feature registry (`backend/ml/preprocessing/feature_registry.py`) — 35 features, frozen
- Preprocessing pipeline (`backend/ml/preprocessing/pipeline.py`) — fitted ColumnTransformer
- Ensemble adapter (`backend/ml/inference/ensemble_adapter.py`) — orchestrates 6 base models
- Scoring service (`backend/app/services/scoring.py`) — routes through ensemble adapter
- Production manifest (`models/registry/production_manifest.json`) — SHA256-verified
- Analytics service (`backend/app/services/analytics.py`) — report-backed, no recomputation
- Any file under `models/` — serialized artifacts with locked checksums

---

## 2. API Contracts (Stable)

### Core Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/health` | Verify backend health and model loading |
| `POST` | `/api/score` | Submit assessment answers → receive credit score |

### Analytics Endpoints (Dashboard)

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/model-stats` | Model metrics table |
| `GET` | `/api/baseline-comparison` | Ensemble vs baselines |
| `GET` | `/api/fairness-report` | Fairness audit results |
| `GET` | `/api/drift-report` | PSI drift report |
| `GET` | `/api/global-importance` | SHAP feature importance |
| `GET` | `/api/score-distribution` | Score histogram |
| `GET` | `/api/roc-data` | ROC curves for all models |
| `GET` | `/api/pr-curve` | Precision-recall curves |
| `GET` | `/api/calibration-curve` | Calibration curves |
| `GET` | `/api/confusion-matrix` | Confusion matrix with derived rates |

### Key Response Details
- `/api/score` returns: `credit_score` (300–850), `risk_band`, `repayment_probability`, `percentile`, `explanation` (top 6 SHAP factors), `counterfactual_actions` (2–3 DICE suggestions), `loan_eligibility`, `improvement_tips`
- All analytics endpoints return pre-computed data — they never trigger model inference
- If an analytics endpoint returns `503`, show "Data not available" in that panel

---

## 3. Explainability Payloads

### SHAP Explanation (in `/api/score` response)
- Array of up to 6 items sorted by absolute importance
- Each item: `feature`, `display_name`, `shap_value`, `direction` (positive/negative), `feature_value`, `plain_language`
- Render as horizontal bars: green for positive, red for negative

### DICE Counterfactual Actions (in `/api/score` response)
- Array of 0–3 actionable improvement suggestions
- Each item: `feature`, `current_value`, `suggested_value`, `estimated_score_gain`, `plain_language`
- Never suggests changing protected attributes (age, gender, region, education)
- Display `plain_language` text to borrowers, not raw feature names

---

## 4. Getting Started

```powershell
# Terminal 1 — Start Backend
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2 — Verify Health
curl http://localhost:8000/api/health
# Should return: "status": "ok", "model_loaded": true

# Terminal 3 — Start Frontend
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

---

## 5. Key Documentation

| Document | Purpose |
|---|---|
| `docs/FRONTEND_INTEGRATION_GUIDE.md` | Complete API integration guide with rendering guidance |
| `docs/API_CONTRACTS.md` | Full request/response schemas |
| `docs/BACKEND_RUNTIME_ARCHITECTURE.md` | Inference flow diagram and frozen systems |
| `docs/DEPLOYMENT.md` | Environment variables and runtime assumptions |
| `docs/RELEASE_AND_GOVERNANCE.md` | Promotion checklists and rollback procedures |

---

## 6. Frontend Responsibilities (Track E)

1. **E.1 Foundation** — Vite/React init, design system, router, landing page
2. **E.2 Assessment** — 27-question flow with 4 sections, behavioral telemetry capture
3. **E.3 Results** — Score gauge, SHAP bars, DICE actions, eligibility, share card
4. **E.4 Polish** — Mobile (375px), loading states, error handling, retry logic
5. **Track F** — Evaluator dashboard with 10 analytics panels (after E)
