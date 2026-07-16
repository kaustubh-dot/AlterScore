# Methodology and model-selection boundary

The public v2 product deliberately does not select or serve a predictive
credit model. It uses a deterministic Financial Decision Readiness rubric
whose question definitions, state transitions, score composition, and
explanation contract are versioned in the v3 plan and backend packages.

## Historical research

The previous synthetic XGBoost, ensemble, NLP, SHAP/DiCE, fairness, and
training work is preserved under `research/legacy_synthetic_model/`. It was a
portfolio research demonstration, not a validated repayment or
creditworthiness model. Labels and fairness reports are synthetic, and AUC
measures recovery of generated data only.

The archived model does not score public assessments. Its files and
dependencies are excluded from the serving import graph and production image.

## Public decision rule

The public score is determined only by the frozen v2 instrument:

- objective correctness contributes 55%;
- four static judgment records and two branching terminal-state scores
  contribute 45%;
- behavior-profile selections and narrative text are unscored;
- the final index is rounded half-up to an integer from 0 through 100;
- the 300–850 value is an explicitly illustrative transformation.

This rubric is educational and does not make a lending, approval, repayment,
or human-validation claim.
