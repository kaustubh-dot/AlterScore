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

<p align="center">
  <img src="docs/assets/readme-illustrations/01-behavioral-evidence.png" alt="Xiaohei turns behavioral evidence into a transparent credit score" width="880">
  <br>
  <em>Behavioral evidence fills the gap when a traditional credit file is empty.</em>
</p>

## How it works

```
Psychometrics ─┐
Telemetry      ├──▶  Feature pipeline  ──▶  Monotonic XGBoost  ──▶  Score + SHAP + counterfactuals
Open-text NLP ─┘                              (governance-gated)
```

<p align="center">
  <img src="docs/assets/readme-illustrations/02-governed-pipeline.png" alt="Xiaohei operates the governed AlterScore scoring pipeline" width="880">
  <br>
  <em>Three evidence streams pass through governance gates before producing a score and explanation.</em>
</p>

Three input streams feed a governed model whose every prediction is checked against:

- **Monotonicity** — improving a positive attribute can never lower the score.
- **Calibration** — predicted probabilities track real default rates (ECE-bounded).
- **Fairness** — subgroup AUC, approval, and calibration gaps are audited and gated.
- **Explainability** — SHAP shows *why*; DiCE shows *what to change*.

## Production model

Manifest-backed, hash-verified runtime — `models/registry/production_manifest.json`.

| Model | Test AUC | Brier | ECE | Drift | Fairness |
|:------|:--------:|:-----:|:---:|:-----:|:--------:|
| `xgboost_monotonic` | 0.779 | 0.177 | 0.035 | stable | passed |

Creditworthiness is driven by hard-to-fake evidence — objective cognition (numeracy, CRT, financial literacy) and scenario psychometrics lead the model — while spoofable process-timing telemetry feeds only the anti-gaming governance layer, never the score.

<p align="center">
  <img src="docs/assets/readme-illustrations/03-governance-guardrails.png" alt="Xiaohei balances the model on governance guardrails" width="880">
  <br>
  <em>The production model is useful only while monotonicity, calibration, fairness, explainability, and verification hold.</em>
</p>

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

<p align="center">
  <img src="docs/assets/readme-illustrations/04-user-workflow.png" alt="Xiaohei walks through the AlterScore run, assessment, features, result, and next step" width="880">
  <br>
  <em>Run the API, complete the assessment, and turn the resulting score into a concrete next step.</em>
</p>

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

[Setup](docs/SETUP.md) · [Deployment](docs/DEPLOYMENT.md) · [API contracts](docs/API_CONTRACTS.md) · [Runtime architecture](docs/BACKEND_RUNTIME_ARCHITECTURE.md) · [Governance workflow](docs/GOVERNANCE_WORKFLOW.md) · [Model registry](docs/MODEL_REGISTRY.md) · [Project structure](docs/PROJECT_STRUCTURE.md)

---

<div align="center">
MIT Licensed
</div>
