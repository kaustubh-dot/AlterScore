# AI Onboarding Template

Use this at the start of every new AI-assisted engineering session.

## Required Reading

Read these files before making changes:

1. `docs/AI_WORKFLOW_RULES.md`
2. `docs/ENGINEERING_CONTEXT.md`
3. `docs/CURRENT_STATE.md`
4. `docs/TODO.md`
5. `docs/DECISIONS.md`
6. Task-specific docs, usually one of:
   - `docs/API_CONTRACTS.md`
   - `docs/DATA_SCHEMA.md`
   - `docs/MODEL_REGISTRY.md`
   - `docs/TESTING_STRATEGY.md`
   - `docs/DEPLOYMENT.md`

## Project Invariants

- Do not use external LLM APIs for the product NLP path.
- Do not use protected attributes as model inputs.
- Do not use `cohort_month` or `application_date` as model inputs.
- Preserve offline training and online inference separation.
- Preserve FastAPI backend and React frontend separation.
- Preserve temporal split: train months 1-8, validation months 9-10, test months 11-12.
- Preserve calibrated stacking ensemble as production model target.
- Preserve SHAP, DICE, fairness, and PSI requirements.

## Session Setup Checklist

- [ ] Confirm current branch.
- [ ] Run `git status --short`.
- [ ] Identify files already changed by others.
- [ ] State the task scope.
- [ ] State the files you expect to edit.
- [ ] Confirm whether docs need updates.
- [ ] Run relevant tests before final response.

## Initial Prompt

```text
You are working on AlterScore, a production-grade alternative credit scoring platform.

Before editing, read:
- docs/AI_WORKFLOW_RULES.md
- docs/ENGINEERING_CONTEXT.md
- docs/CURRENT_STATE.md
- docs/TODO.md
- docs/DECISIONS.md
- any task-specific docs

Do not implement outside the requested scope.
Do not use protected attributes as model inputs.
Do not introduce external LLM APIs.
Keep offline ML training separate from online inference.

Task:
[paste task here]

Expected output:
[files, tests, docs, or explanation needed]
```
