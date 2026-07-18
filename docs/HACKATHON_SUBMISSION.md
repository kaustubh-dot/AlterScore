# Hackathon submission kit

## Project name

AlterScore — Explainable Financial Readiness

## Project description

AlterScore helps students and first-time earners understand how prepared they are for everyday financial decisions. Instead of returning an opaque number, it combines short financial calculations with branching scenarios and produces a deterministic 0–100 readiness index, worked evidence, practical next steps, and a publicly verifiable signed summary. It is an educational tool, not a credit score or lending system.

## Repository

https://github.com/kaustubh-dot/AlterScore

## Live demo

https://alterscore.vercel.app/

Judges can select **Preview a sample result** on the first screen for a 60-second overview, then take the full assessment if time allows.

## Tech stack

React 19, Vite, FastAPI, Pydantic, Python 3.12, Vercel, Hugging Face Spaces, GitHub Actions, pytest, Node test runner, Web Crypto, and HMAC-SHA256 signed verification.

Codex was used throughout planning, implementation, repository review, test creation, debugging, and end-to-end verification.

## Challenges faced

The hardest part was making an explainable financial assessment useful without letting it become a disguised credit or lending system. We kept the scoring rubric deterministic and server-owned, separated unscored reflection from scored evidence, protected hidden answer authority with one-time attempts, and returned a signed result whose calculation and recommendations can be reconciled. We also had to make detailed evidence understandable on mobile while keeping the full flow anonymous and resilient across separate frontend and backend deployments.

## Demo video: 2–3 minute shot list

1. **0:00–0:15 — Problem:** Financial quizzes usually end with a number but do not show how decisions created it.
2. **0:15–0:35 — Product:** Open the landing page and use the sample-result preview to show the outcome immediately.
3. **0:35–1:20 — Assessment:** Show one calculation, one judgement item, and two connected stages of a branching simulation.
4. **1:20–1:55 — Result:** Show the readiness index, exact contribution reconciliation, recommendation evidence, and decision replay.
5. **1:55–2:20 — Trust:** Open the public signed verification response and explain that identity, credit history, and optional reflection never affect the score.
6. **2:20–2:40 — Codex:** Briefly explain how Codex supported implementation, review, tests, and release verification.
7. **2:40–3:00 — Close:** Re-state the audience and the educational boundary.

## Pitch deck: six slides

1. **Problem:** A score without evidence does not teach better financial decisions.
2. **Solution:** Calculations + branching choices + explainable readiness result.
3. **Live product:** Three screenshots: assessment, simulation, result.
4. **Architecture:** React → FastAPI → deterministic scorer → signed explanation.
5. **Trust and differentiation:** Anonymous attempts, unscored reflection, public verification, no lending use.
6. **Impact and roadmap:** Financial-literacy programs, learner progress over time, and externally validated assessment research.

## Final submission checklist

- Confirm the repository, live app, video, and deck open in a signed-out browser.
- Record the video after the production deployment matches the submitted commit.
- Put the live demo and video links above the fold in the repository README.
- Use a public YouTube link or a Drive link set to “Anyone with the link.”
- Keep the video under three minutes and show the result in the first 40 seconds.
- Test the backend once shortly before submission so a cold start does not consume judging time.
- Do not describe AlterScore as a credit score, underwriting model, or repayment predictor.
