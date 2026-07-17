# Reusable Codex phase-review prompt

Paste the following prompt into a Codex chat after Luna finishes any phase.

```text
Review the latest completed Luna phase for AlterScore.
Commit and push only when the user explicitly authorizes those operations.

Workspace:
C:\Kaustubh\Projects\AlterScore

Required branch:
codex/scoring-production-hardening

Before reviewing, read these files completely:

1. C:\Kaustubh\Projects\AlterScore\docs\SCORING_V3_LUNA_PLAN.md
2. C:\Kaustubh\Projects\AlterScore\docs\SCORING_V3_CURRENT_STATE.md
3. C:\Kaustubh\Projects\AlterScore\docs\SCORING_V3_CHECKPOINTS.md

Determine the phase awaiting review from the current-state document and the
latest Luna implementation checkpoint.

Scope and safety:

- Review only the completed phase; do not implement the next phase.
- Preserve every existing task-related and user-owned worktree change.
- Do not reset, clean, checkout, switch branches, or discard files.
- Treat Luna and subagent test claims as unverified until independently checked.
- Inspect the recorded subagent tasks, file ownership, findings, and Luna
  verification. Confirm no overlapping concurrent writes or unauthorized shared
  contract/tracking/git changes occurred. If the checkpoint lacks enough
  provenance to prove this, record that limitation instead of inventing it.
- Prefer lightweight subagents for independent read-only searches, test execution,
  reference tracing, bundle inspection, and dependency/documentation audits.
  Keep scoring, security, shared-contract decisions, tracking, fixes, git, and
  integration under the primary Codex reviewer.

Review procedure:

1. Confirm branch, HEAD, dirty state, and exact phase scope.
2. Compare the implementation with every Luna-work item, invariant, required
   test, acceptance criterion, and review gate for that phase.
3. Inspect all added, modified, deleted, and archived files.
4. Search for logical errors, scoring loopholes, hidden assumptions, regressions,
   privacy/security issues, stale compatibility behavior, and scope violations.
5. Run the relevant tests independently and add focused adversarial, property,
   boundary, contract, or browser checks where appropriate.
6. Run git diff --check and confirm Luna did not start the next phase.

Review decision and corrections:

- Choose exactly one review decision: PASS or CHANGES REQUIRED.
- PASS requires every phase gate to be satisfied with no required work left.
- On CHANGES REQUIRED, list every finding with priority, file/line evidence,
  impact, and exact correction; keep the same phase active and stop.
- Luna normally performs corrections within the same phase and appends another
  implementation checkpoint. Do not implement them unless the user explicitly
  authorizes Codex to do so.
- Explicit correction authority is limited to the reviewed phase and does not
  authorize Phase N+1, commit, push, deployment, or checkpoint-history rewrites.
- If Codex is explicitly authorized to correct the phase, add regression
  coverage as needed, rerun the focused and phase-wide checks, and append a
  separate correction checkpoint before re-reviewing.

Phase-specific emphasis:

- Phase 0: baseline accuracy, frozen-spec consistency, inventory completeness,
  and proof that scoring behavior did not change.
- Phase 1: arithmetic, deterministic generation, exact scoring, server-only
  keys, serialization secrecy, and unknown-ID rejection.
- Phase 2: exhaust all branches, terminal-state correctness, monotonicity,
  dominance, no arbitrary totals, and no double-counting.
- Phase 3: formulas, equal scenario weighting, bounds, determinism, invariance,
  and contribution reconciliation.
- Phase 4: token tampering, replay races, cross-attempt answers, expiry, atomic
  consumption, signed verification, rate limits, logging privacy, and readiness.
- Phase 5: frontend/API parity, StrictMode, retries, stale state, error recovery,
  accessibility, responsive behavior, and bundle secrecy.
- Phase 6: explanation arithmetic, worked solutions, branching replay,
  recommendation evidence, rubric leakage, accessibility, and claims.
- Phase 7: public/research isolation, v1 retirement, dependencies, dead
  references, artifacts, docs, and readiness independence.
- Phase 8: required CI, release parity, readiness, deployment gating,
  credentials failure, smoke checks, and rollback.
- Phase 9: complete regression, threat model, documentation, release readiness,
  and unresolved blockers.

Decision recording:

1. On PASS, update SCORING_V3_CURRENT_STATE.md to mark the reviewed phase Passed,
   set Phase N+1 as the single immediate next action, append a Codex PASS
   checkpoint, and update the phase tracker. Commit/push is not a prerequisite
   to Luna beginning that approved successor from the preserved uncommitted
   worktree after its handoff. Codex does not begin Phase N+1.
2. On CHANGES REQUIRED, update SCORING_V3_CURRENT_STATE.md accordingly, keep
   Phase N active, append a CHANGES REQUIRED checkpoint, and update the phase
   tracker. Do not begin Phase N+1.
3. If, and only if, the user explicitly authorizes it, stage only reviewed
   task-related changes, create an intentional phase commit using a concise
   conventional message, and push `codex/scoring-production-hardening`.
   Otherwise leave the worktree uncommitted and report that commit/push were not
   authorized.
4. If a push was authorized, verify it succeeded and report the commit SHA.

Final response must include:

- phase reviewed;
- final decision: PASS or CHANGES REQUIRED;
- findings ordered by severity and, if explicitly authorized, the fixes;
- independent commands/tests and exact results;
- subagent-review summary;
- tracking files updated;
- commit SHA and push result when PASS and explicitly authorized; otherwise
  state that they were not authorized;
- exact next action.
```
