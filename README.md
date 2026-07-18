# AlterScore

> A financial-readiness assessment that explains the score, shows the evidence, and suggests the next useful step.

[![Hackathon build](https://img.shields.io/badge/Hackathon-Built%20with%20Codex-111111?style=for-the-badge)](https://openai.com/codex/)
[![CI](https://img.shields.io/github/actions/workflow/status/kaustubh-dot/AlterScore/ci.yml?branch=main&style=for-the-badge&label=CI)](https://github.com/kaustubh-dot/AlterScore/actions/workflows/ci.yml)
[![Live](https://img.shields.io/badge/Live-Try%20AlterScore-00C2A8?style=for-the-badge)](https://alterscore.vercel.app/)

**[Open the live app](https://alterscore.vercel.app/)** · **[Take the 2-minute quick trial](https://alterscore.vercel.app/assessment?mode=trial)** · **[Preview a sample result](https://alterscore.vercel.app/#sample-result)**

AlterScore helps students, first-time earners, and people building confidence with money understand how they handle practical financial decisions. Instead of returning an unexplained number, it connects the result to calculations, decision paths, evidence, and concrete areas to improve.

## Judge it in two minutes

1. Open the **[quick trial](https://alterscore.vercel.app/assessment?mode=trial)**.
2. Answer five practical financial questions.
3. Inspect the instant readiness snapshot, domain breakdown, and response-by-response guidance.
4. From the result, open the full assessment to see the server-issued, signed experience.

No login, documents, identity data, device fingerprint, or credit history is required.

## The problem

Financial-literacy quizzes often stop at right or wrong. Credit products often produce high-impact outputs that users cannot inspect. Neither is a good way to help someone practise making better decisions.

AlterScore takes a narrower, safer approach:

- test financial knowledge with practical calculations;
- carry financial state through branching decisions;
- explain every displayed contribution and recommendation;
- keep identity and credit history outside the scoring boundary;
- clearly avoid lending, approval, and creditworthiness decisions.

<p align="center">
  <img src="docs/assets/readme-xiaohei/01-evidence-not-identity.png" alt="Financial knowledge and decisions enter a fixed scoring rubric while identity remains outside" width="880">
  <br>
  <em>Knowledge and decisions go in. Identity stays out.</em>
</p>

## What we built

### Quick trial

A five-question, client-side preview for judges and first-time visitors. It produces immediate domain feedback and answer guidance in roughly two minutes. The result is deliberately labelled **illustrative and unsigned**.

### Full assessment

A server-issued assessment combining:

- financial calculations;
- static decision-judgement items;
- three-stage branching simulations;
- optional, explicitly unscored reflection prompts.

The backend validates opaque response IDs, consumes the attempt once, applies a deterministic rubric, and returns an explainable 0–100 Financial Decision Index. A redacted projection is signed with HMAC-SHA256 and can be verified through the public API.

<p align="center">
  <img src="docs/assets/readme-xiaohei/02-branching-decisions.png" alt="A branching choice changes the financial state inherited by the next decision" width="880">
  <br>
  <em>A choice changes the state inherited by the next choice.</em>
</p>

## Why it stands out

| Capability | What the user gets |
| --- | --- |
| Stateful scenarios | Decisions have visible downstream consequences instead of isolated multiple-choice scoring. |
| Inspectable evidence | Domain scores, calculation contributions, simulation replay, and recommendations can be opened and checked. |
| Verifiable result | The full assessment returns a signed, redacted summary with a public verification route. |
| Privacy-first flow | No account, identity, device profile, documents, or credit history enters the score. |
| Accessible experience | Keyboard focus management, reduced-motion support, responsive layouts, safe-area handling, and usable touch targets. |
| Honest product boundary | The UI repeatedly states that AlterScore is educational—not a lender or approval system. |

<p align="center">
  <img src="docs/assets/readme-xiaohei/03-explainable-results.png" alt="An explainable score includes its calculation, evidence, and next step" width="880">
  <br>
  <em>The score is only the start: calculation, evidence, and next step travel with it.</em>
</p>

## Built with Codex

Codex was the engineering collaborator behind this hackathon build. It was used to:

- audit the existing repository and trace frontend/backend contracts;
- implement the quick-trial and judge-friendly product path;
- improve responsive behavior across mobile, tablet, and desktop;
- find UI failures through browser-based visual inspection;
- harden accessibility, reduced-motion behavior, and destructive-action flows;
- write and run focused contract, explainability, separation, and release tests;
- inspect diffs and keep changes scoped before deployment.

There is intentionally **no runtime AI dependency** in the assessment. Codex helped build and verify the product; it does not secretly generate questions, judge users, or calculate their score. The scoring path remains deterministic and auditable.

## Architecture

```text
                     ┌─────────────────────────────┐
Quick trial ────────▶│ React + Vite               │──▶ Illustrative result
                     │ responsive assessment UI    │
                     └──────────────┬──────────────┘
                                    │ HTTPS
                                    ▼
                     ┌─────────────────────────────┐
Full assessment ───▶ │ FastAPI v2                 │
                     │ one-time attempt lifecycle │
                     └──────────────┬──────────────┘
                                    ▼
                     ┌─────────────────────────────┐
                     │ Deterministic rubric       │
                     │ + explainability pipeline  │
                     └──────────────┬──────────────┘
                                    ▼
                       Signed, verifiable result
```

| Layer | Technology | Location |
| --- | --- | --- |
| Interface | React 19, Vite 8, CSS, Lucide | [`frontend/`](frontend/) |
| API | Python 3.12, FastAPI, Pydantic | [`backend/app/`](backend/app/) |
| Scoring | Deterministic objective and branching rubric | [`backend/app/unified_scoring/`](backend/app/unified_scoring/) |
| Integrity | One-time bearer attempts, HMAC-SHA256 result signing | [`backend/app/api/v2/`](backend/app/api/v2/) |
| Quality | Pytest, Node contract tests, ESLint, GitHub Actions | [`tests/`](tests/) and [`frontend/tests/`](frontend/tests/) |
| Deployment | Vercel frontend, containerized backend | [`deploy/`](deploy/) and [`Dockerfile`](Dockerfile) |

The detailed transport contract is documented in [`docs/API_CONTRACTS.md`](docs/API_CONTRACTS.md).

## Hardest engineering challenges

### Explainability without leaking authority

The browser needs enough evidence to explain a result, but it must not receive hidden answer keys or the scoring rubric. The API therefore returns a bounded explanation projection after a one-time submission rather than shipping scoring authority to the client.

### Stateful decisions that reconcile

Each branching scenario carries a financial state from one stage to the next. The displayed replay, domain contribution, and final index must reconcile with the same deterministic path.

### Secure one-time attempts in a modern React lifecycle

Attempt issuance, cancellation, retries, and submission had to remain safe under React Strict Mode, slow networks, route transitions, and expired attempts without accidentally consuming a form twice.

### A polished interface across real viewports

The final pass covered 320, 390, 768, 1024, 1280, and 1440 pixel widths. It fixed overlapping controls, undersized touch targets, short-screen modals, safe areas, route focus, reduced motion, and confirmation before destructive actions.

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

Set `ALTERSCORE_SIGNING_SECRET` to a generated base64url secret. Set `VITE_API_BASE_URL` when the API is not available at the frontend's default local address. Production builds additionally require `VITE_RELEASE_SHA`; see [`frontend/README.md`](frontend/README.md).

## Verify the build

```bash
# Backend
python -m pip install -r backend/requirements.txt
python -m pip install -r backend/requirements-dev.txt
python -m pytest tests/unit/backend tests/integration/api

# Frontend
cd frontend
npm run lint
npm run test:phase5
npm run test:phase6
npm run test:phase7
npm run test:phase8
```

CI also checks the serving image, API contract, explainability invariants, release boundaries, and frontend production build.

## What comes next

- More scenario packs covering budgeting, borrowing, savings, and irregular income.
- Localized financial language and currency-aware examples.
- Longitudinal progress that preserves the current privacy boundary.
- User testing with students and first-time earners before any claim of educational effectiveness.

## Safety boundary

AlterScore is an educational demonstration. It is not a lender, credit bureau, underwriting system, repayment predictor, financial adviser, approval tool, or source of credit offers. It must not be used for lending, eligibility, pricing, approval, denial, or any other high-impact financial decision.

## License

Released under the [MIT License](LICENSE). The community-oriented project history remains available on the [`oss-main`](https://github.com/kaustubh-dot/AlterScore/tree/oss-main) branch.
