# AlterScore Scoring Roadmap

This roadmap turns the scoring backend from a strong prototype into a production-grade decisioning system. The current backend now has a calibrated, manifest-backed monotonic runtime with blocking promotion gates passing; the remaining quality work is monitoring, drift investigation, and richer score-band evidence.

## Phase 0: Immediate Hardening

Status: complete.

- Require explicit opt-in for `/api/debug-score`.
- Validate scenario option IDs against the specific scenario field.
- Run a startup preprocess/predict probe for single-model runtime artifacts.
- Align counterfactual gains with the governed probability used for the displayed score.

## Phase 1: Score Calibration

Goal: make `repayment_probability`, `credit_score`, risk bands, and loan ranges mean something measurable.

- Train and persist a calibration layer for the promoted model. Status: calibrated monotonic XGBoost now uses isotonic calibration persisted in `models/artifacts/xgboost_monotonic.pkl`.
- Store score-mapping parameters in the production manifest instead of hard-coding the log-odds transform. Status: manifest-backed `score_mapping` is now used by runtime scoring and counterfactual score gains.
- Generate approval/default-rate tables by score band.
- Add tests that fail if expected calibration error exceeds the promotion threshold. Status: promotion gates enforce ECE from `models/reports/metrics_monotonic.json`.
- Expose both `model_probability` and `governed_probability` in internal logs.

Exit criteria:

- Test ECE is below the agreed threshold.
- Every risk band has observed repayment/default statistics.
- Score mapping is versioned with the model artifact.

## Phase 2: Promotion Gates

Goal: prevent artifacts from being treated as promotion-clean when reports say "review before promotion."

- Add a promotion-gate evaluator for AUC, calibration, drift, subgroup fairness, individual fairness, and governance impact. Status: initial backend evaluator and health exposure implemented.
- Make manifest promotion status derive from gate results. Status: calibrated manifest is now `promoted` only because blocking gates pass.
- Fail CI if a promoted manifest references reports that fail blocking gates. Status: `python -m backend.ml.registry.promotion_gates` now returns non-zero for promoted manifests with failing/unevaluated gates; use `--require-clean-pass` for release-candidate promotion checks.
- Add a health warning when production artifacts are stale or fail advisory gates.

Exit criteria:

- A promoted manifest cannot coexist with failing individual fairness or calibration gates.
- Gate thresholds are stored in a versioned policy file. Status: `models/registry/promotion_gate_policy.json` now backs API health and CLI checks.
- Non-blocking warnings stay visible. Status: PSI is currently `watch` at `0.2052` on `avg_response_time_ms`, below the blocking `0.30` alert threshold.

## Phase 3: Model Quality

Goal: improve predictive quality without sacrificing explainability.

- Compare monotonic XGBoost against calibrated stacking, logistic regression, and residual MLP using the same promotion gates.
- Keep monotonic constraints where product/legal explainability requires them.
- Add ablation tests for psychometric, behavioral, and text features.
- Replace weak text heuristics with evaluated local embeddings or remove text-derived score impact until validated.
- Investigate the response-time PSI watch: decide whether `avg_response_time_ms` drift is expected synthetic seasonality, an input-generation artifact, or a signal that should be reduced in model influence.

Exit criteria:

- The selected model is justified by a written tradeoff: predictive performance, calibration, fairness, stability, and explainability.
- Important feature groups have documented incremental value.

## Phase 4: Runtime Monitoring

Goal: know when production behavior drifts.

- Log model version, score, probabilities, risk band, governance multiplier, and feature-drift summaries without storing raw answers.
- Add daily/weekly PSI and score-distribution monitors.
- Add latency and artifact-load checks.
- Alert on score-band approval swings and governance penalty spikes.

Exit criteria:

- Drift and scoring quality reports can be regenerated from production logs.
- Runtime alerts distinguish model drift, input drift, and infrastructure failure.

## Phase 5: Responsible Decisioning

Goal: make the project credible as a lending-adjacent system.

- Separate user-facing coaching from eligibility decisions.
- Add adverse-action style reason codes backed by stable feature contributions.
- Document protected-attribute exclusions and proxy-risk review.
- Add privacy retention rules for logs and debug traces.
- Add a manual-review path for borderline scores.

Exit criteria:

- User-visible explanations are stable, auditable, and not just raw SHAP text.
- The system has a documented policy for when not to automate a decision.
