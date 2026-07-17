# Data and feature policy

The public v2 assessment is not a model feature pipeline. It is a deterministic
server-owned instrument whose structured answer values are scored directly by
the unified rubric.

## Issued assessment data

Each form contains exactly:

- eight parameterized integer objective items;
- four static single-choice judgment items;
- six branching single-choice stages across two scenarios;
- six unscored behavior-profile items;
- one optional unscored narrative configuration.

The server retains the internal answer key, exact static rubric, and branching
transition definitions in memory for the single issued attempt. The public form
contains only prompts, response kinds, required flags, and shuffled opaque
option identifiers.

## Scoring data

Objective correctness is an exact integer comparison. Judgment scoring uses the
four static principle rubrics and two terminal-state branching scores. The
financial index is the frozen 55% objective / 45% judgment weighted total,
rounded half-up to an integer. Behavior selections and narrative text do not
enter any score, recommendation, or readiness decision.

Each terminal-state branch score is feasible-range normalized with exact
rational arithmetic before it enters the six-component judgment mean. The
original weighted terminal-dimension composite and the scenario's exhaustive
attainable endpoints remain internal diagnostics. Public results expose the
normalized score, its `feasible_range_normalized` basis, the four safe terminal
dimensions, and plain-language interpretation without exposing per-option or
per-path scoring authority.

The signed explanation may expose safe worked values, state-before / delta /
state-after timelines, terminal dimensions, principle-level guidance, and
evidence-linked recommendations. It never exposes answer keys, option IDs,
private rubric tables, hidden transition constants, raw submission maps, or
user-indexed history.

## Archived research data

Synthetic labels, generated datasets, model artifacts, SHAP/DiCE payloads,
NLP features, fairness reports, and training metadata are preserved under
`research/legacy_synthetic_model/`. They are offline reference material only.
Archived labels and fairness reports are synthetic; archived AUC measures
recovery of generated data and is not external validation or repayment
evidence. The archived model does not score public assessments.

## Excluded from the public contract

The public service does not accept or score browser telemetry, timing, focus,
scroll, device, protected attributes, temporal metadata, semantic text
features, embeddings, sentiment, language style, model probabilities, or
synthetic percentiles. The public contract makes no lending, creditworthiness,
approval, or repayment claim.
