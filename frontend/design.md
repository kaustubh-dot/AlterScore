# AlterScore frontend design boundary

This document describes the active public v2 assessment experience. The
historical model-dashboard design is preserved at
`research/legacy_synthetic_model/source/frontend/design-legacy.md` and is not
part of the production frontend.

## Product surface

AlterScore presents an anonymous, server-issued readiness assessment. The
frontend renders the instrument returned by the API, submits opaque option
IDs, and displays the signed result and its explainability projection. The
browser is a presentation client; it does not own score formulas, model
artifacts, answer keys, or hidden rubric fields.

The active routes are:

- `/` — public landing and assessment entry point.
- `/assessment` — server-issued assessment form.
- `/results` — signed, session-bound result and explanation view.
- `/research` — direct-link-only static Research Lab disclosure.

There is no public admin dashboard. Research material must remain visibly
separate from the assessment flow and must not read assessment state, call
research APIs, or imply that archived experiments score public assessments.

## Visual direction

The interface uses a calm dark instrumentation palette, restrained indigo and
cyan accents, high-contrast typography, and motion only where it communicates
progress or state. Cards, labels, and status text should make the current
assessment state clear without exposing internal scoring mechanics or raw
option identifiers.

## Accessibility and privacy

Every interactive state needs a visible focus treatment, semantic labels, and a
useful live-region announcement where content changes asynchronously. Do not
persist bearer tokens, raw responses, option IDs, or hidden rubric fields in
durable browser storage. The static Research Lab must remain usable without
network access and must disclose that its labels and fairness reports are
synthetic, its AUC measures recovery of generated data, and its model does not
score public assessments.
