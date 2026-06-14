<div align="center">

# AlterScore

**Governed behavioral credit scoring for thin-file and unbanked borrowers.**

Scores creditworthiness from psychometrics, behavioral telemetry, and language — not borrowing history — under enforced fairness, calibration, and monotonicity gates.

[![Live API](https://img.shields.io/badge/API-Hugging%20Face-yellow?style=flat-square&logo=huggingface)](https://huggingface.co/spaces/CooLBoT22/alterscore-backend)
[![Build](https://img.shields.io/github/actions/workflow/status/kaustubh-dot/AlterScore/ci.yml?branch=main&style=flat-square&logo=github)](https://github.com/kaustubh-dot/AlterScore/actions)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=white)

</div>

---

## Why

Traditional underwriting excludes ~1.4 billion adults who lack a formal credit history. AlterScore replaces *"what have you borrowed before?"* with *"how do you reason, decide, and follow through?"* — turning a five-minute assessment into a calibrated 300–850 score with a transparent reason for every point.

## How it works

```
Psychometrics ─┐
Telemetry      ├──▶  Feature pipeline  ──▶  Monotonic XGBoost  ──▶  Score + SHAP + counterfactuals
Open-text NLP ─┘                              (governance-gated)
```

Three input streams feed a governed model whose every prediction is checked against:

- **Monotonicity** — improving a positive attribute can never lower the score.
- **Calibration** — predicted probabilities track real default rates (ECE-bounded).
- **Fairness** — subgroup AUC, approval, and calibration gaps are audited and gated.
- **Explainability** — SHAP shows *why*; DiCE shows *what to change*.

## Production model

Manifest-backed, hash-verified runtime — `models/registry/production_manifest.json`.

| Model | Test AUC | Brier | ECE | Drift | Fairness |
|:------|:--------:|:-----:|:---:|:-----:|:--------:|
| `xgboost_monotonic` | 0.758 | 0.184 | 0.035 | stable | passed |

> Trained on a synthetic dataset for demonstration. Not for real lending decisions.

## Quickstart

**Backend** (Python 3.12):

```bash
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r backend/requirements.txt
python -m spacy download en_core_web_sm
uvicorn backend.app.main:app --reload --port 8000
```

Health: `http://127.0.0.1:8000/api/health` · Docs: `http://127.0.0.1:8000/docs`

**Frontend** (Node 20):

```bash
cd frontend && npm install && npm run dev
```

**Tests:**

```bash
ALTERSCORE_ENV=test pytest        # backend
cd frontend && npm run lint && npm run build
```

## Layout

| Path | Contents |
|:-----|:---------|
| `backend/` | FastAPI app, ML scoring, governance, request logging |
| `frontend/` | React + Vite SPA (assessment flow, results, analytics dashboard) |
| `models/` | Production manifest, preprocessors, model binaries |
| `tests/` | Unit, integration, and API contract suites |
| `docs/` | Architecture, governance, and API references |

## Deployment

- **Backend** → Hugging Face Spaces (Docker) via GitHub Actions on push to `main`.
- **Frontend** → Vercel via its GitHub integration on push to `main`.

## Docs

[Project structure](docs/PROJECT_STRUCTURE.md) · [Governance workflow](docs/GOVERNANCE_WORKFLOW.md) · [Model selection](docs/MODEL_SELECTION_DECISIONS.md) · [API contracts](docs/API_CONTRACTS.md) · [Setup](docs/SETUP.md)

---

<div align="center">
MIT Licensed
</div>
