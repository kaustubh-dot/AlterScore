# Hackathon submission kit

## Project name

AlterScore — Explainable Financial Readiness

## One-line pitch

AlterScore turns everyday financial decisions into an explainable readiness profile: it shows not only the index a learner received, but which calculation, judgement, trade-off, and state transition produced it.

## Project description

AlterScore helps students and first-time earners practise decisions involving cash flow, obligations, reserves, borrowing, delayed payments, and uncertain income. It is deliberately educational. It does not make lending, underwriting, credit, eligibility, or repayment predictions.

The product combines four parts:

1. Short objective calculations test whether a learner can reason about basic financial quantities.
2. Judgement items test how a learner weighs competing priorities rather than selecting a memorised “correct” sentence.
3. Connected branching simulations mutate a canonical financial state after each decision. Later prompts inherit the consequences of earlier choices.
4. The result explains the evidence, exposes the scoring contributions, identifies the highest-impact weakness, and gives practical next steps.

The full assessment returns a deterministic 0–100 readiness index with a server-signed explanation. The judge preview is an unsigned, local educational simulation using the same branching dimensions at a smaller scale.

## Links

### Repository

https://github.com/kaustubh-dot/AlterScore

### Live demo

https://alterscore.vercel.app/

Judges can select **Start assessment** on the first screen and choose between **Quick trial · 5 questions** and **Full assessment**. The quick trial takes approximately two to three minutes. The full assessment is the calibrated, server-signed path.

## What judges should notice

- The product has a meaningful preview route, but the preview is not an easy five-question quiz.
- The quick trial displays the live financial state entering each decision: cash, payment remaining, reserve, and accumulated cost.
- Each answer changes the next state. A different collection, payment, borrowing, or reserve choice produces a different later problem.
- There are no fixed 20-point questions in the trial. The terminal state is scored across the same four branching dimensions used by the main assessment.
- The result explains state changes, opportunity cost, path potential, terminal dimensions, recommendations, and the boundary between an illustrative preview and a verified full result.
- The full assessment adds objective items, static judgement items, multiple connected simulations, server-side scoring, signed explanations, and public verification.

## Judge walkthrough

### A. Quick trial: two-to-three minutes

1. Open the live demo and click **Start assessment**.
2. Choose **Quick trial · 5 questions**.
3. Read the state strip before answering the first question. It shows the starting operating cash, payment remaining, emergency reserve, and cost to date.
4. Work through the five connected stages:

   - **Collection decision:** convert a receivable into verified cash, balancing immediate liquidity against a settlement concession.
   - **Funding decision:** respond to the payment shortfall using operating cash, the emergency reserve, or priced bridge borrowing.
   - **Payment decision:** decide how much to apply immediately versus retaining enough liquidity for the rest of the plan.
   - **Resilience decision:** fund an essential operating shock, explicitly defer part of it, or finance it at a visible cost.
   - **Opportunity decision:** evaluate a supplier opportunity after the remaining receivable settles, using the state created by all four prior decisions.

5. Change an earlier answer with the **Back** control if desired. Downstream answers are cleared and recalculated so stale choices cannot survive a changed state.
6. Submit the trial and inspect the result:

   - readiness index and path band;
   - obligation coverage, liquidity retention, cost efficiency, and plan feasibility;
   - cash, payment remaining, reserve, and accumulated cost at the terminal state;
   - recommendations prioritised by the weakest high-impact dimension;
   - **Review the state replay**, which shows the selected decision, best reachable move from that state, retained path potential, changed fields, protected value, and trade-off.

### B. Full assessment: five-to-eight minutes

1. Return to the assessment chooser and select **Full assessment**.
2. Complete the required objective calculations and judgement items.
3. Follow the connected simulations. The full path uses the same immutable state-transition approach, but with more scenarios and server-owned scoring authority.
4. Review the result’s formula waterfall, worked objective evidence, judgement evidence, branching timelines, recommendations, limitations, and signed verification details.
5. Use the public verification surface to demonstrate that the displayed result can be checked without exposing raw responses or identity data.

### C. Suggested judge path

If time is limited, take the quick trial first, deliberately choose one reserve-preserving option and one borrowing-heavy option in separate attempts, then compare the terminal cost and liquidity dimensions. This demonstrates that the result is path-sensitive and not a count of right answers. If time remains, use the full assessment to inspect signed explainability.

## Scoring and explainability

### Quick trial formula

The trial replays every selected transition from a fixed initial state. At the terminal state it computes:

- **40% obligation coverage:** required payments met divided by required payments due.
- **25% liquidity retention:** unencumbered liquidity retained after accounting for unpaid obligations.
- **20% cost efficiency:** remaining efficiency after borrowing costs and avoidable costs.
- **15% plan feasibility:** whether retained liquidity and confirmed inflows can fund the remaining plan, adjusted for late-payment events.

The raw composite is normalized between the weakest and strongest reachable trial paths. There are five stages with three options each, producing 243 reachable paths. A decision therefore affects the terminal profile through the state it creates; it does not carry an isolated mark.

Because one short scenario cannot provide the same evidence depth as the full assessment, the displayed preview index applies a limited-evidence adjustment: 70% of the feasible-range path score plus a 30% neutral anchor. This keeps the trial useful for comparison without presenting a lucky five-choice path as a high-confidence 90+ readiness result. The result shows both the underlying path score and the adjusted preview index.

### Full assessment formula

The full assessment keeps the same explainable branching model and adds objective and static judgement evidence. The canonical scorer combines the objective component and judgement component using the server-owned weighting, preserves exact fractions until display rounding, and returns a signed explanation. The frontend never becomes an authority for hidden full-assessment answers or server-signed results.

### Result explanation

Every result is designed to answer four questions:

1. What did the learner choose?
2. What state did that choice create?
3. What did the choice protect, and what trade-off did it introduce?
4. Which next action would improve the highest-impact weakness?

The full result additionally reconciles the displayed formula, objective evidence, judgement components, scenario dimensions, recommendations, limitations, and verification metadata.

## Trust, privacy, and educational boundaries

- AlterScore is not a credit score, underwriting model, lender, or repayment predictor.
- Trial results are explicitly labelled illustrative and unsigned.
- Full scoring authority remains server-owned.
- Raw responses are not used as a public identity profile.
- Optional reflection is separated from scored evidence.
- Recommendations are tied to observed weaknesses, not generic motivational text.
- Public verification checks the signed summary without exposing raw submissions.
- The UI communicates limitations so judges and learners do not mistake an educational index for a financial decision made about them.

## Accessibility, resilience, and UX work

- Question headings receive focus after stage changes for keyboard and screen-reader users.
- Radio controls remain native and labelled by the complete decision text.
- Progress is exposed as an accessible progressbar.
- The trial state strip keeps the key numbers visible while the decision text changes.
- Result cards collapse into a readable replay disclosure on smaller screens.
- The chooser clearly separates the quick preview from the full signed assessment.
- The legacy loading animation is restored for a consistent transition into the app.
- Trial results are stored safely for the route transition and cleaned when malformed or stale.
- Earlier trial bugs involving black/empty result transitions were tested through a complete browser walkthrough and route reload.

## Tech stack

React 19, Vite, FastAPI, Pydantic, Python 3.12, Vercel, Hugging Face Spaces, GitHub Actions, pytest, Node test runner, Web Crypto, session-safe browser storage, and HMAC-SHA256 signed verification.

Codex was used throughout planning, implementation, repository review, test creation, debugging, UI refinement, and end-to-end verification.

## Challenges faced

The central challenge was making a financial assessment teachable without turning it into a disguised credit or lending system. We kept the rubric deterministic, separated reflection from scored evidence, protected hidden answer authority with one-time attempts, and returned a signed result whose calculation and recommendations can be reconciled.

A second challenge was making the judge preview credible. A linear quiz with equal marks made it too easy and did not represent the product’s core insight. The current trial is therefore a replayable five-stage simulation with explicit state transitions, feasible-range normalization, and result evidence that shows how one decision caused the next constraint.

A third challenge was presenting dense evidence without making the UI feel like a spreadsheet. The current design uses a compact state strip during assessment, a four-dimension terminal summary, progressive disclosure for replay details, and responsive layouts for narrow screens.

## Demo video: two-to-three-minute shot list

1. **0:00–0:15 — Problem:** Financial quizzes usually end with a number but do not show how decisions created it.
2. **0:15–0:35 — Product:** Open the landing page, open the assessment chooser, and show the quick-trial and full-assessment routes.
3. **0:35–1:20 — Trial assessment:** Show the live state strip, answer the first two stages, and pause on the changed cash/payment state before continuing.
4. **1:20–1:55 — Trial result:** Show the readiness index, four terminal dimensions, terminal cash and obligations, formula, recommendations, and the expanded state replay.
5. **1:55–2:20 — Full assessment and trust:** Open the full assessment result or verification surface and explain signed scoring, anonymity, limitations, and the non-lending boundary.
6. **2:20–2:40 — Implementation:** Briefly explain how Codex supported implementation, UI review, tests, debugging, and release verification.
7. **2:40–3:00 — Close:** Re-state the audience, educational purpose, and roadmap.

## Pitch deck: seven slides

1. **Problem:** A score without evidence does not teach better financial decisions.
2. **Solution:** Calculations + judgement + connected branching choices + explainable readiness result.
3. **Live product:** Show the assessment chooser, a trial state strip, and the terminal result.
4. **Judge walkthrough:** Show the exact four-step path: choose Quick trial → make a state-changing decision → observe the next inherited state → expand the state replay. Add a small before/after example such as “₹24,000 cash before funding decision → ₹14,000 after a ₹10,000 payment choice.”
5. **Scoring and architecture:** React → FastAPI → immutable state transitions → deterministic scorer → signed explanation. Include the trial’s 40/25/20/15 branching weights, 243-path feasible-range normalization, and the transparent limited-evidence preview adjustment.
6. **Trust and differentiation:** Anonymous attempts, unscored reflection, public verification, no lending use, unsigned illustrative trial, and server-owned full assessment authority.
7. **Impact and roadmap:** Financial-literacy programs, learner progress over time, classroom feedback loops, and externally validated assessment research.

### Pitch-deck judge walkthrough speaker notes

“Start assessment opens two routes. The quick trial is not five isolated questions: each answer changes the financial state shown on the next screen. We can see cash, unpaid obligations, reserve, and accumulated cost before choosing again. At the end, the same branching dimensions used by the main assessment score the terminal state. Opening the replay shows exactly what changed, what the decision protected, what it cost, and which move would have preserved more reachable potential. The full route adds server-signed evidence and public verification.”

## Final submission checklist

- Confirm the repository, live app, video, and deck open in a signed-out browser.
- Record the video after the production deployment matches the submitted commit.
- Put the live demo and video links above the fold in the repository README.
- Use a public YouTube link or a Drive link set to “Anyone with the link.”
- Keep the video under three minutes and show the result in the first 40 seconds.
- Test the backend shortly before submission so a cold start does not consume judging time.
- Verify the quick trial end to end: chooser → five stateful decisions → trial result → expanded state replay → retry/full-assessment handoff.
- Verify that changing an earlier answer clears downstream answers and changes the later state.
- Verify a full-assessment path through result explanation and public signature verification.
- Run the frontend trial-path test, phase contract tests, lint, and production build against the submitted commit.
- Check mobile-width screenshots for the chooser, state strip, terminal summary, and replay disclosure.
- Do not describe AlterScore as a credit score, underwriting model, or repayment predictor.
