# AlterScore

> A transparent, deterministic financial decision-readiness demonstration.

[![CI](https://github.com/kaustubh-dot/AlterScore/actions/workflows/ci.yml/badge.svg)](https://github.com/kaustubh-dot/AlterScore/actions/workflows/ci.yml)

**[Try the live demo](https://alterscore.vercel.app/)** · **[Read the API contract](docs/API_CONTRACTS.md)** · **[Contribute](CONTRIBUTING.md)**

AlterScore is a public project for exploring financial decision readiness through an explainable, answer-based assessment. It is designed to make the assessment experience understandable: scoring is deterministic, server-owned, and accompanied by a reconciliation of the result.

<p align="center">
  <img src="docs/assets/readme-xiaohei/01-evidence-not-identity.png" alt="Xiaohei turns financial knowledge and decisions into a readiness score while identity stays outside the scoring boundary" width="880">
  <br>
  <em>AlterScore scores financial knowledge and decisions—not identity or credit history.</em>
</p>

## Important boundaries

AlterScore is a demonstration, not a lender, credit bureau, underwriting tool, approval system, repayment predictor, financial product, or source of credit offers. It must not be used to make lending, creditworthiness, approval, denial, or other high-impact financial decisions.

The application does not use behavioral answers or the optional narrative to calculate a score. Historical labels, fairness reports, and model evaluation materials were synthetic; they are not external validation.

## What is included

- An anonymous v2 assessment with objective items, static judgment items, financial-state simulations, and unscored reflection prompts.
- A deterministic 0–100 Financial Decision Index with an illustrative 300–850 transform.
- A React frontend with explainable results and a session-only dashboard.
- A FastAPI backend with signed results, one-time bearer attempts, bounded in-memory verification, and HTTPS-only remote token transport.
- CI checks covering linting, contracts, release boundaries, backend tests, and the serving image.

<p align="center">
  <img src="docs/assets/readme-xiaohei/02-branching-decisions.png" alt="Xiaohei makes a branching choice that changes the financial state inherited by the next decision" width="880">
  <br>
  <em>Each branching choice changes the financial state that the next decision inherits.</em>
</p>

## Architecture

```text
React assessment → FastAPI v2 API → deterministic scorer → signed, explainable result
```

| Area | Location |
| --- | --- |
| Public API, assessment instrument, and scorer | [`backend/app/`](backend/app/) |
| React assessment and results experience | [`frontend/`](frontend/) |
| Tests | [`tests/`](tests/) |
| API, deployment, rollback, and methodology docs | [`docs/`](docs/) |

<p align="center">
  <img src="docs/assets/readme-xiaohei/03-explainable-results.png" alt="Xiaohei pulls an explanation showing a score calculation, supporting evidence, and next step" width="880">
  <br>
  <em>A score arrives with its calculation, supporting evidence, and a practical next step.</em>
</p>

## Run locally

Requirements: Python 3.12 and Node.js `20.19.x` or `>=22.12.0`.

```bash
# Terminal 1: backend
python -m venv venv
# Windows: venv\Scripts\activate
python -m pip install -r backend/requirements.txt
python -m uvicorn backend.app.main:app --reload --port 8000

# Terminal 2: frontend
cd frontend
npm install
npm run dev
```

Set `ALTERSCORE_SIGNING_SECRET` to a generated base64url secret before using the assessment. The frontend uses `VITE_API_BASE_URL` to find the API; see the [frontend README](frontend/README.md) for the local override and production-build requirements.

## Verify changes

```bash
python -m pip install -r backend/requirements.txt
python -m pip install -r backend/requirements-dev.txt
python -m pytest tests/unit/backend tests/integration/api

cd frontend
npm run lint
npm run test:phase5
npm run test:phase6
npm run test:phase7
npm run test:phase8
```

For a production build, set `VITE_RELEASE_SHA` to the reviewed backend commit SHA before running `npm run build`. The [deployment guide](docs/DEPLOYMENT.md) and [rollback checklist](docs/ROLLBACK_CHECKLIST.md) describe the release process.

## Contributing

<p align="center">
  <img src="docs/assets/readme-xiaohei/04-open-source-contributions.png" alt="Xiaohei fits code, tests, documentation, and review into one open-source toolbox" width="880">
  <br>
  <em>Reliable contributions fit code, tests, documentation, and review into one working whole.</em>
</p>

Contributions that improve clarity, accessibility, security, tests, documentation, and the assessment experience are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.

## License

AlterScore is available under the [MIT License](LICENSE).
