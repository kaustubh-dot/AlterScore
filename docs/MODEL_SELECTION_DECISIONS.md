# Model Selection Decisions

## Final Direction

The active production-track architecture is now a governed monotonic
`XGBoost` runtime.

## Why Monotonic XGBoost Won

It is currently the strongest balance of:

- predictive performance
- monotonic consistency
- pairwise counterfactual stability
- fairness gate compliance
- calibration quality
- operational simplicity
- explainability and auditability

In the governed full-scale comparison it achieved:

- AUC `0.8090`
- Brier `0.1496`
- ECE `0.0207`
- monotonic gate: passed
- pairwise counterfactual gate: passed
- fairness gate: passed
- promotion eligible: `true`

## Why the Previous Ensemble Is No Longer the Preferred Architecture

The earlier calibrated stacking ensemble remains valuable as a checked-in
benchmark and rollback/reference path, but it is no longer the default runtime
because the constrained-tree production path:

- materially outperformed it on AUC
- materially improved calibration
- provided stronger monotonic and counterfactual guarantees
- aligned better with governance-first production goals

## Why TabNet Is Research-Only

TabNet remains important as a benchmark and as a research lesson, but it is not
the trusted production scorer because governance audits showed that:

- raw TabNet could achieve acceptable aggregate AUC while still failing local
  monotonic behavior
- pairwise counterfactual audits exposed behavior that AUC alone did not catch
- repeated repair and curriculum experiments improved robustness but did not
  make raw TabNet stable enough for promotion

That conclusion is itself valuable and should remain part of presentations and
final project material.

## Fairness Hardening Outcome

Focused fairness hardening on the monotonic `XGBoost` candidate found that:

- conservative proxy regularization and clipping can reduce the small
  `gender=non_binary` subgroup calibration gap somewhat
- however, the baseline raw monotonic `XGBoost` still remains the strongest
  production-safe overall operating point

## Current Checked-In Runtime Caveat

The promoted checked-in monotonic bundle reports AUC `0.8040`, Brier `0.1514`,
ECE `0.0284`, stable PSI, and a fairness attention item for
`gender=non_binary`. The next production-readiness task is to reconcile these
checked-in reports with the stronger governed full-run review before any pilot
claim.

## Decision Rule Going Forward

Future challengers must beat the current leading candidate under the same
governance requirements, not just on headline accuracy.
