# AlterScore AI Workflow Rules

## Purpose

This is the mandatory operating procedure for any AI agent or coding assistant working on AlterScore. Follow this file before, during, and after every task.

These rules exist to prevent context drift, accidental architecture changes, protected-attribute leakage, undocumented schema changes, and half-finished implementation work.

## Priority Order

When instructions conflict, follow this order:

1. Direct user instruction in the current conversation.
2. Safety and repository preservation rules.
3. `docs/AI_WORKFLOW_RULES.md`.
4. `docs/ENGINEERING_CONTEXT.md`.
5. Task-specific docs such as API, data, model, deployment, and testing docs.
6. Existing code patterns.

Do not silently ignore conflicts. If a conflict affects implementation, record it in the final response and update docs when appropriate.

## Startup Protocol

Before editing files, every AI agent must:

1. Run `git status --short`.
2. Identify existing uncommitted files.
3. Assume uncommitted changes may belong to the user.
4. Read the required docs:
   - `docs/AI_WORKFLOW_RULES.md`
   - `docs/ENGINEERING_CONTEXT.md`
   - `docs/CURRENT_STATE.md`
   - `docs/ROADMAP.md`
   - `docs/TODO.md`
5. Read task-specific docs:
   - API or backend task: `docs/API_CONTRACTS.md`
   - Data or feature task: `docs/DATA_SCHEMA.md`
   - Model or training task: `docs/MODEL_REGISTRY.md` and `docs/EXPERIMENT_LOG.md`
   - Deployment task: `docs/DEPLOYMENT.md`
   - Testing task: `docs/TESTING_STRATEGY.md`
6. State the task scope.
7. Identify the files likely to change.
8. Proceed only within the requested scope.

## Non-Negotiable Project Rules

- Do not use external LLM APIs for product NLP.
- Do not use protected attributes as model inputs.
- Do not use `cohort_month` or `application_date` as model inputs.
- Use the canonical 35 model inputs: 33 numeric plus 2 categorical.
- Keep protected attributes for fairness audit only.
- Preserve train months 1-8, validation months 9-10, and test months 11-12.
- Keep offline ML training separate from online inference.
- Keep FastAPI backend and React frontend separated.
- Build contracts and schemas before route or UI implementation.
- Build data and ML reports before dashboard visualization.
- Never invent architecture that contradicts the PRD or accepted decisions.

## Implementation Protocol

For every implementation task:

1. Work on one bounded module at a time.
2. Prefer existing repository structure and docs over new structure.
3. Keep edits small and aligned with the current milestone.
4. Add or update tests with implementation changes.
5. Add or update docs when behavior, contracts, schemas, artifacts, or workflow changes.
6. Avoid unrelated refactors.
7. Avoid monolithic files.
8. Keep training code out of API routes.
9. Keep inference code independent from notebooks.
10. Keep frontend client scoring secondary to backend source-of-truth scoring.

## Documentation Update Protocol

Update docs in the same task when the corresponding area changes.

| Change Type | Required Docs |
|---|---|
| Architecture decision | `docs/DECISIONS.md` |
| Current status or next step | `docs/CURRENT_STATE.md`, `docs/TODO.md` |
| API request/response schema | `docs/API_CONTRACTS.md` |
| Feature list, target, data shape, split, protected fields | `docs/DATA_SCHEMA.md` |
| Model artifact, metrics, promotion, registry | `docs/MODEL_REGISTRY.md` |
| Training experiment | `docs/EXPERIMENT_LOG.md` |
| Test policy or required gates | `docs/TESTING_STRATEGY.md` |
| Deployment, environment, artifact packaging | `docs/DEPLOYMENT.md` |
| Roadmap or ordering | `docs/ROADMAP.md` |
| AI handoff/process | `docs/AI_WORKFLOW_RULES.md` and templates if needed |

Do not leave docs stale after changing contracts or architecture.

## Testing Protocol

Before final response:

1. Run the smallest relevant test set for the files changed.
2. For documentation-only changes, at minimum verify file presence and search for obvious stale contradictions.
3. Never claim tests passed unless they were actually run.
4. If tests cannot be run, say why.
5. If implementation changes are made without tests, explain the residual risk.

Recommended test progression:

1. Feature registry tests.
2. Schema tests.
3. Data validation tests.
4. NLP and feature engineering tests.
5. Preprocessing and split-integrity tests.
6. Model smoke tests.
7. API integration tests.
8. Frontend and E2E tests.

## Git Protocol

### Before Editing

- Run `git status --short`.
- Note existing uncommitted files.
- Do not overwrite or revert user changes.
- If a file has unrelated user edits, work around them or ask if the conflict blocks the task.

### Branching

- Default AI branch prefix: `codex/`.
- Branch format: `codex/<scope>-<short-task>`.
- Create or switch branches only when asked or when the workflow explicitly requires it.

### Committing

- Do not commit unless the user asks for a commit or the agreed workflow requires a checkpoint commit.
- Before committing:
  - Run relevant tests.
  - Check `git diff`.
  - Ensure docs are updated.
  - Ensure no generated datasets, model binaries, secrets, or local logs are staged accidentally.
- Use Conventional Commits:
  - `docs: ...`
  - `feat: ...`
  - `fix: ...`
  - `test: ...`
  - `chore: ...`
  - `refactor: ...`

### Staging

- Stage only files related to the task.
- Do not stage `.env`, model binaries, generated datasets, large reports, caches, or logs unless explicitly requested.

## Session Close Protocol

Before ending a task, provide a concise summary with:

- What changed.
- Files changed.
- Tests or verification run.
- Docs updated.
- Any blockers or risks.
- Next recommended step.

If the task changed project status, update `docs/CURRENT_STATE.md`.
If the task completed or added work items, update `docs/TODO.md`.
If another model or future session will continue the work, use `docs/context_templates/SESSION_SUMMARY_TEMPLATE.md` or `docs/context_templates/TASK_HANDOFF_TEMPLATE.md`.

## AI Agent Prompt Template

Use this when starting a new AI session:

```text
You are working on AlterScore.

First read:
- docs/AI_WORKFLOW_RULES.md
- docs/ENGINEERING_CONTEXT.md
- docs/CURRENT_STATE.md
- docs/ROADMAP.md
- docs/TODO.md
- task-specific docs

Run git status before editing.
Preserve the canonical 35 model inputs.
Do not use protected attributes as model inputs.
Do not use external LLM APIs.
Keep offline ML training separate from online inference.
Add or update tests for implementation changes.
Update docs when contracts, schemas, architecture, models, deployment, or project status change.

Task:
[paste task here]
```

## Definition Of Done

A task is done only when:

- The requested scope is complete.
- Relevant files are updated.
- Relevant docs are updated.
- Relevant tests or verification were run, or limitations are clearly stated.
- No unrelated user changes were reverted.
- The final response includes the next practical step.

