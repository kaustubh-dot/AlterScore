# AlterScore

AlterScore is a synthetic, answer-based Financial Decision Readiness
demonstration. It is not a lender, credit bureau, underwriting tool, approval
system, repayment predictor, financial product, or source of credit offers.

## Public scoring boundary

The public application uses the anonymous v2 contract:

- eight deterministic objective items;
- four principle-level static judgment items;
- two three-stage financial-state simulations;
- six unscored behavior-profile items and an optional unscored narrative;
- a 0–100 Financial Decision Index and an illustrative 300–850 transform.

The v2 scorer is deterministic and server-owned. Forms use opaque identifiers,
single-use bearer attempts, signed results, bounded in-memory verification, and
HTTPS-only token transport. Behavior and narrative never affect the score.

The former `POST /api/score` and `/api/debug-score` routes return `410 Gone`.
Former analytics routes are not public. The production repository and runtime
do not include model artifacts, SHAP/DiCE, NLP, training scripts, or the
retired scorer. Historical source remains recoverable from Git history and the
pre-production backup branch.

## Local development

Backend (Python 3.12):

```bash
python -m venv venv
# Windows: venv\Scripts\activate
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.app.main:app --reload --port 8000
```

Set `ALTERSCORE_SIGNING_SECRET` to a generated base64url secret before using
the assessment. Remote and production-like v2 form and score requests require
HTTPS; loopback HTTP is accepted only for local/test/development startup. The
process probe is `/api/live`; readiness is `/api/ready`.

Frontend (Node 20.19.x or >=22.12.0):

```bash
cd frontend
npm install
npm run dev
```

Validation:

```bash
python -m pip install -r backend/requirements.txt
python -m pip install -r backend/requirements-dev.txt
python -m pytest tests/unit/backend tests/integration/api
cd frontend && npm run lint && VITE_RELEASE_SHA=<40-character-reviewed-sha> npm run build && npm run test:phase5 && npm run test:phase6 && npm run test:phase7 && npm run test:phase8
```

Production builds must use the exact backend SHA in `VITE_RELEASE_SHA`.
The inline assignment uses POSIX shell syntax; in PowerShell run
`$env:VITE_RELEASE_SHA = '<40-character-reviewed-sha>'` before
`npm.cmd run build`.
See `docs/DEPLOYMENT.md` and `docs/ROLLBACK_CHECKLIST.md` for CI-gated
deployment, semantic readiness, smoke, and paired rollback procedures.

## Repository layout

| Path | Purpose |
| --- | --- |
| `backend/app/` | Public v2 API, canonical instrument, branching engine, and unified scorer |
| `frontend/` | React assessment, result explainability, dashboard, and static Research Lab |
| `tests/` | Public v2, instrument, branching, unified-scoring, and retirement coverage |
| `docs/` | Active contracts, runtime, deployment, rollback, and methodology references |

The removed historical labels and fairness reports were synthetic. Any
historical AUC measured recovery of generated data, not external validation.
No historical model scores public assessments.
